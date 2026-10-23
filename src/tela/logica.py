"""Normalização e estatísticas puras da tela local."""

import hashlib
import json
from datetime import date
from statistics import median

from statsmodels.stats.proportion import proportion_confint

PERGUNTAS_DEMO = (
    {"id": "E-A", "pergunta": "O que os clientes relatam sobre entregas atrasadas?",
     "k": 10, "nota_min": None, "nota_max": 2, "situacao": "atrasado",
     "categoria": None, "compra_de": None, "compra_ate": None,
     "hash": "28fb0e20214f31f163156580e6a1f3fddfcd18c6fa71fc890e5a607506b40a88"},
    {"id": "E-B", "pergunta": "O que os clientes relatam que aconteceu depois que a entrega atrasou?",
     "k": 10, "nota_min": None, "nota_max": 2, "situacao": "atrasado",
     "categoria": None, "compra_de": None, "compra_ate": None,
     "hash": "72ea2402264ac2f80a6a7c3ea043a10de4b72209b6eddb07f53b2c1435bf68ec"},
    {"id": "P15", "pergunta": "Qual é o prazo oficial de reembolso da Olist quando uma entrega atrasa?",
     "k": 10, "nota_min": None, "nota_max": 2, "situacao": "atrasado",
     "categoria": None, "compra_de": None, "compra_ate": None,
     "hash": "c53daa6570b52c72f4a9b289b7ae87d21be989beac77b7af34f9c729a8684e24"},
)

MENSAGENS_STATUS = {
    "respondida": "Resposta com fontes citadas",
    "sem_evidencia": "Sem evidência nos relatos: o sistema recusou responder",
    "erro_geracao": "Falha do serviço de geração (não é recusa)",
}


def mensagem_status(status: str) -> str:
    return f"{MENSAGENS_STATUS[status]} ({status})" if status in MENSAGENS_STATUS else status


def hash_confere(colado: str, previa: str) -> bool:
    """Compara exatamente o texto que será passado ao servidor, inclusive espaços."""
    return colado == previa


def _opcional(valor):
    if valor is None or valor == "" or valor == "Todos":
        return None
    return valor


def _data(valor):
    valor = _opcional(valor)
    if valor is None:
        return None
    if isinstance(valor, date):
        return valor.isoformat()
    return date.fromisoformat(str(valor)).isoformat()


def argumentos_responder(pergunta, k, nota_min, nota_max, situacao, categoria,
                         compra_de, compra_ate) -> dict:
    """Produz exatamente os argumentos de busca passados pelo main do CLI."""
    return {"pergunta": pergunta, "k": int(k), "nota_min": _opcional(nota_min),
            "nota_max": _opcional(nota_max),
            "situacao_entrega": _opcional(situacao),
            "categoria": _opcional(categoria),
            "compra_de": _data(compra_de), "compra_ate": _data(compra_ate)}


def chave_entrada(args: dict) -> str:
    bruto = json.dumps(args, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), default=str)
    return hashlib.sha256(bruto.encode("utf-8")).hexdigest()


def resumo_execucoes(linhas: list[dict]) -> dict:
    tentativas = [linha for linha in linhas if linha.get("tipo") == "tentativa"]
    erros = sum(bool(linha.get("erro_integracao")) for linha in tentativas)
    duracoes = [linha["duracao_ms"] for linha in tentativas
                if not linha.get("erro_integracao")
                and isinstance(linha.get("duracao_ms"), (int, float))]
    n = len(tentativas)
    ic = proportion_confint(erros, n, method="wilson") if n else (None, None)
    status = {}
    for linha in linhas:
        if linha.get("tipo") == "resultado":
            nome = linha.get("status", "sem_status")
            status[nome] = status.get(nome, 0) + 1
    outros = sum(linha.get("tipo") not in {"envio", "tentativa", "resultado"}
                 or "classe_operacional" in linha for linha in linhas)
    return {"tentativas": n, "erros_integracao": erros,
            "taxa_erro": erros / n if n else None, "ic95_wilson": ic,
            "mediana_duracao_ms_sem_erro": median(duracoes) if duracoes else None,
            "resultados_por_status": status, "linhas_outro_formato": outros}
