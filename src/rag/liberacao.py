"""Prévia, hash de liberação, alerta de PII, orçamento diário e registro do envio ao Gemini."""
import hashlib
import json
import re
from datetime import datetime
from pathlib import Path

from src.eval.avaliar_geracao import _canonico, configuracao_execucao

TETO_DIARIO = 20
# Cada pergunta pode gastar até duas chamadas (ADR 0007); a reserva evita passar do teto.
RESERVA_POR_PERGUNTA = 2
RAIZ = Path(__file__).resolve().parents[2]
ARQUIVOS_CODIGO = ("src/demo.py", "src/rag/liberacao.py", "src/rag/responder.py",
                   "src/rag/provedor_gemini.py", "src/rag/tentativas.py")
# Ordem importa: CNPJ e CPF antes de telefone, que casaria parte dos mesmos dígitos.
PADROES_PII = (
    ("email", re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")),
    ("cnpj", re.compile(r"\b\d{2}\.?\d{3}\.?\d{3}/\d{4}-?\d{2}\b")),
    ("cpf", re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b|\b\d{11}\b")),
    ("cep", re.compile(r"\b\d{5}-\d{3}\b")),
    ("telefone", re.compile(r"\(?\b\d{2}\)?\s?9?\d{4}[-\s]\d{4}\b")),
)


class EnvioBloqueado(ValueError):
    """Envio recusado antes de qualquer chamada externa."""


def digest_codigo() -> dict:
    return {nome: hashlib.sha256((RAIZ / nome).read_bytes()).hexdigest()
            for nome in ARQUIVOS_CODIGO}


def montar_payload(pergunta: str, filtros: dict, evidencias: list[dict]) -> dict:
    # Tudo que muda o que sai da máquina ou como a resposta é gerada entra no hash.
    return {"pergunta": pergunta.strip(), "filtros": filtros,
            "contexto": [{"review_id": e["review_id"], "texto": e["texto"]} for e in evidencias],
            "configuracao": configuracao_execucao(repetir_transitorios=True),
            "codigo": digest_codigo()}


def hash_payload(payload: dict) -> str:
    return hashlib.sha256(_canonico(payload).encode("utf-8")).hexdigest()


def alertas_pii(pergunta: str, evidencias: list[dict]) -> list[dict]:
    """Heurística informativa: nome próprio e endereço por extenso passam; leitura humana segue obrigatória."""
    alertas = []
    for origem, texto in [("pergunta", pergunta)] + [(e["review_id"], e["texto"]) for e in evidencias]:
        restante = texto
        tipos = []
        for tipo, padrao in PADROES_PII:
            if padrao.search(restante):
                tipos.append(tipo)
                restante = padrao.sub(" ", restante)
        if tipos:
            alertas.append({"origem": origem, "tipos": tipos})
    return alertas


def _ler_registro(caminho: Path) -> list[dict]:
    if not caminho.exists():
        return []
    linhas = []
    for numero, linha in enumerate(caminho.read_text(encoding="utf-8").splitlines(), 1):
        if not linha.strip():
            continue
        try:
            item = json.loads(linha)
        except json.JSONDecodeError as erro:
            raise ValueError(f"Registro corrompido na linha {numero}; orçamento não pode ser calculado.") from erro
        if not isinstance(item, dict) or "tipo" not in item or "execucao" not in item:
            raise ValueError(f"Registro sem tipo/execução na linha {numero}.")
        linhas.append(item)
    return linhas


def chamadas_no_dia(caminho: Path, agora: datetime) -> int:
    """Conta chamadas do dia UTC; envio sem resultado (processo caiu) reserva o máximo."""
    dia = agora.date().isoformat()
    linhas = _ler_registro(caminho)
    tentativas = {l["execucao"]: l.get("tentativas") for l in linhas if l["tipo"] == "resultado"}
    total = 0
    for envio in (l for l in linhas if l["tipo"] == "envio"):
        if not str(envio.get("utc", "")).startswith(dia):
            continue
        usadas = tentativas.get(envio["execucao"])
        total += usadas if type(usadas) is int and 0 <= usadas <= RESERVA_POR_PERGUNTA else RESERVA_POR_PERGUNTA
    return total


def restantes_hoje(caminho: Path, agora: datetime) -> int:
    return max(TETO_DIARIO - chamadas_no_dia(caminho, agora), 0)


def exigir_liberacao(digest: str, aprovacao_sha256, caminho: Path, agora: datetime) -> None:
    if not isinstance(aprovacao_sha256, str) or aprovacao_sha256 != digest:
        raise EnvioBloqueado("hash ausente ou diferente da prévia; gere nova prévia e revise o contexto")
    usadas = chamadas_no_dia(caminho, agora)
    if usadas + RESERVA_POR_PERGUNTA > TETO_DIARIO:
        raise EnvioBloqueado(f"orçamento diário esgotado ({usadas}/{TETO_DIARIO} chamadas no dia UTC)")


class Registro:
    """JSONL só por anexação; cabeçalho gravado antes da API para sobreviver a queda."""

    def __init__(self, caminho: Path, execucao: str, relogio):
        self.caminho = caminho
        self.execucao = execucao
        self.relogio = relogio

    def _anexar(self, tipo: str, dados: dict) -> None:
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        linha = {"tipo": tipo, "execucao": self.execucao,
                 "utc": self.relogio().isoformat(), **dados}
        with self.caminho.open("a", encoding="utf-8") as arquivo:
            arquivo.write(json.dumps(linha, ensure_ascii=False, allow_nan=False) + "\n")
            arquivo.flush()

    def envio(self, dados: dict) -> None:
        self._anexar("envio", dados)

    def tentativa(self, evento: dict) -> None:
        self._anexar("tentativa", evento)

    def resultado(self, dados: dict) -> None:
        self._anexar("resultado", dados)
