"""Avaliação local com contexto curado; compatibilidade de status não é acerto.

O hash declara revisão/autorização manual pelo operador, não prova autorização
criptográfica. O manifesto proposto ainda exige liberação explícita do lote.
"""
import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from src.rag.provedor_gemini import GeradorGemini, INSTRUCAO, MODELO_GERACAO, SCHEMA_RESPOSTA
from src.rag.responder import Resposta, responder


def _exigir(condicao: bool) -> None:
    if not condicao:
        raise ValueError("Manifesto fora do contrato.")


def _texto(valor) -> bool:
    return isinstance(valor, str) and bool(valor.strip())


def validar_manifesto(manifesto: dict) -> None:
    _exigir(isinstance(manifesto, dict) and set(manifesto) ==
            {"schema_version", "modo", "modelo", "estado", "casos"})
    _exigir(type(manifesto["schema_version"]) is int and manifesto["schema_version"] == 1)
    _exigir(manifesto["modo"] == "contexto_curado" and manifesto["modelo"] == MODELO_GERACAO
            and manifesto["estado"] == "proposta")
    casos = manifesto["casos"]
    _exigir(isinstance(casos, list) and len(casos) == 20)
    ids = []
    for caso in casos:
        _exigir(isinstance(caso, dict) and set(caso) ==
                {"id", "origem", "pergunta", "evidencias", "fontes_locais",
                 "criterio_proposto", "status_esperados"})
        cid = caso["id"]
        _exigir(isinstance(cid, str) and cid in {f"E{i:02d}" for i in range(1, 21)})
        ids.append(cid)
        origem = "sintetico" if cid == "E19" else "controle_local" if cid == "E20" else "real"
        _exigir(caso["origem"] == origem and _texto(caso["pergunta"])
                and _texto(caso["criterio_proposto"]))
        evidencias = caso["evidencias"]
        _exigir(isinstance(evidencias, list) and (not evidencias if cid == "E20" else bool(evidencias)))
        aliases = []
        for evidencia in evidencias:
            _exigir(isinstance(evidencia, dict) and set(evidencia) == {"review_id", "texto"})
            alias = evidencia["review_id"]
            _exigir(isinstance(alias, str) and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", alias)
                    is not None and _texto(evidencia["texto"]))
            aliases.append(alias)
        _exigir(len(set(aliases)) == len(aliases))
        fontes = caso["fontes_locais"]
        _exigir(isinstance(fontes, dict))
        if origem == "real":
            _exigir(set(fontes) == set(aliases) and all(isinstance(v, str) and
                    re.fullmatch(r"[0-9a-fA-F]{32}", v) is not None for v in fontes.values()))
        else:
            _exigir(fontes == {})
        estados = caso["status_esperados"]
        _exigir(isinstance(estados, list) and bool(estados) and
                all(isinstance(s, str) and s in {"respondida", "sem_evidencia"} for s in estados))
        _exigir(len(set(estados)) == len(estados))
        if cid in {"E13", "E14", "E15", "E16", "E19", "E20"}:
            _exigir(estados == ["sem_evidencia"])
    _exigir(len(set(ids)) == 20)


def carregar_manifesto(caminho: Path) -> dict:
    def pares_unicos(pares):
        resultado = {}
        for chave, valor in pares:
            if chave in resultado:
                raise ValueError("Chave repetida no manifesto.")
            resultado[chave] = valor
        return resultado
    manifesto = json.loads(Path(caminho).read_text(encoding="utf-8"), object_pairs_hook=pares_unicos)
    validar_manifesto(manifesto)
    return manifesto


def configuracao_geracao() -> dict:
    return {"modelo": MODELO_GERACAO, "prompt": INSTRUCAO, "schema": SCHEMA_RESPOSTA,
            "temperature": 0, "max_output_tokens": 512, "response_mime_type": "application/json", "timeout": 25000,
            "attempts": 1, "versao_sdk": version("google-genai")}


def _canonico(valor) -> str:
    return json.dumps(valor, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def hash_lote(manifesto: dict) -> str:
    validar_manifesto(manifesto)
    return hashlib.sha256(_canonico({"manifesto": manifesto, "configuracao":
                                   configuracao_geracao()}).encode("utf-8")).hexdigest()


def previa(manifesto: dict) -> dict:
    return {"tipo": "previa", "hash_lote": hash_lote(manifesto), "configuracao": configuracao_geracao(),
            "manifesto": manifesto, "aviso": "Proposta pendente: o hash declara autorização manual; "
            "não comprova revisão nem libera este lote. Apenas pergunta e evidências vão ao provedor."}


def _criar_gerador():
    from google import genai
    from google.genai import types
    client = genai.Client(http_options=types.HttpOptions(
        timeout=25000, retry_options=types.HttpRetryOptions(attempts=1)))
    return GeradorGemini(client=client, contexto_revisado=True), client


def _erro_seguro(erro: Exception, fase: str) -> dict:
    codigo = getattr(erro, "code", None)
    return {"classe": type(erro).__name__, "codigo": codigo if type(codigo) is int else None,
            "fase": fase}


def _saida_serializavel(saida):
    try:
        _canonico(saida)
        return saida
    except (TypeError, ValueError):
        return {"tipo_nao_serializavel": type(saida).__name__}


def executar(manifesto: dict, *, aprovacao_sha256: str, previsao: int,
             saida: Path, gerar=None) -> None:
    # Cópia congelada impede alteração do lote durante a rodada.
    validar_manifesto(manifesto)
    manifesto = json.loads(_canonico(manifesto))
    digest = hash_lote(manifesto)
    if not isinstance(aprovacao_sha256, str) or aprovacao_sha256 != digest:
        raise ValueError("Hash de aprovação não corresponde ao lote.")
    if type(previsao) is not int or not 0 <= previsao <= 20:
        raise ValueError("Previsão deve ser inteiro entre 0 e 20.")
    caminho = Path(saida)
    if not caminho.parent.is_dir():
        raise ValueError("Pasta de saída precisa existir.")
    if gerar is not None and not callable(gerar):
        raise ValueError("Gerador inválido.")
    client = None
    with caminho.open("x", encoding="utf-8") as arquivo:
        def registrar(valor):
            arquivo.write(_canonico(valor) + "\n")
            arquivo.flush()
        registrar({"tipo": "cabecalho", "hash_lote": digest, "configuracao": configuracao_geracao(),
                   "manifesto": manifesto, "previsao": previsao,
                   "utc": datetime.now(timezone.utc).isoformat()})
        try:
            if gerar is None:
                gerar, client = _criar_gerador()
            for caso in manifesto["casos"]:
                captura = {"saida_provedor": None, "erro_integracao": None}
                def capturar(pergunta, evidencias):
                    try:
                        resultado = gerar(pergunta, evidencias)
                        captura["saida_provedor"] = _saida_serializavel(resultado)
                        return resultado
                    except Exception as erro:
                        captura["erro_integracao"] = _erro_seguro(erro, "gerador")
                        raise
                try:
                    resposta = responder(caso["pergunta"], caso["evidencias"], capturar)
                except Exception as erro:
                    captura["erro_integracao"] = _erro_seguro(erro, "validacao_aplicacao")
                    resposta = Resposta("erro_geracao", "Saída inválida do modelo.")
                registrar({"tipo": "caso", "id": caso["id"], **captura,
                           "resposta_aplicacao": asdict(resposta),
                           "status_esperado_compativel": resposta.status in caso["status_esperados"],
                           "julgamento_semantico": "pendente", "tentativa": 1})
            registrar({"tipo": "fim", "casos_registrados": len(manifesto["casos"])})
        finally:
            if client is not None:
                client.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifesto", required=True, type=Path)
    parser.add_argument("--executar", action="store_true")
    parser.add_argument("--aprovacao-sha256")
    parser.add_argument("--previsao", type=int)
    parser.add_argument("--saida", type=Path)
    argumentos = parser.parse_args(argv)
    try:
        manifesto = carregar_manifesto(argumentos.manifesto)
        if argumentos.executar:
            if argumentos.saida is None:
                raise ValueError("Informe saída nova para executar.")
            executar(manifesto, aprovacao_sha256=argumentos.aprovacao_sha256,
                     previsao=argumentos.previsao, saida=argumentos.saida)
        else:
            print(json.dumps(previa(manifesto), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError):
        print("Falha: confira contrato, aprovação, previsão e arquivo de saída.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
