"""Avaliação local com contexto curado; compatibilidade de status não é acerto.

O hash declara revisão/autorização manual pelo operador, não prova autorização
criptográfica. O manifesto proposto ainda exige liberação explícita do lote.
"""
import argparse
import hashlib
import json
import re
import sys
from collections import Counter
from dataclasses import asdict
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from src.rag.provedor_gemini import GeradorGemini, INSTRUCAO, MODELO_GERACAO, SCHEMA_RESPOSTA
from src.rag.responder import Resposta, responder
from src.rag.tentativas import GeradorComTentativas, politica_tentativas
from src.rag.tentativas import CODIGOS_TRANSITORIOS

# Primeiras tentativas julgáveis da rodada 04; spec 0008 registra fonte, exclusões e B=0/13.
IDS_PAREAVEIS_BASELINE = frozenset({"E02", "E03", "E04", "E06", "E07", "E08", "E09",
                                    "E10", "E11", "E12", "E14", "E15", "E18"})
LIMIAR_PAREADO = 3  # B_pareado + 3; B=0 para qualquer subconjunto destes IDs.
LIMIAR_ABSOLUTO = 5
HASH_REAVALIACAO_LOCAL = "203ec986dd98ec4550490df3b8418f5c42acf74187006b1767e2e52c3b76fae3"
IDS_REAVALIACAO_LOCAL = frozenset({"E02", "E03", "E04", "E06", "E07", "E08", "E09",
                                  "E10", "E11", "E12"})
CAPTURA_FALHA_LOCAL = Path(__file__).resolve().parents[2] / "reports/geracao_citacao_afirmacao_fase1_20261019.jsonl"
SHA256_CAPTURA_FALHA_LOCAL = "44c87c8f5ad60531b8172de85ab8d46767305b17b2d13c8cec4297445960a199"
HASH_REAVALIACAO_SERVICO = "203ec986dd98ec4550490df3b8418f5c42acf74187006b1767e2e52c3b76fae3"
CAPTURAS_FALHA_SERVICO = {
    "E02": ("reports/geracao_citacao_afirmacao_f1_e1_e02_20261020.jsonl",
            "86d265867b737551b72dc7b0f5b419cf4f89171df8109959360c9267376047bb", 2),
    "E18": ("reports/geracao_citacao_afirmacao_f1_e14-e15-e18_20261020T1421.jsonl",
            "47b65861713f7f74a208a8575f0db2124dd679f6a3e401d24656fd384925272a", 1),
}


def autorizar_reenvio_servico(ids: list[str], digest: str, envios: Counter,
                             resultados: dict) -> None:
    """Confere a autorização pontual antes de criar o cliente ou a captura nova."""
    if digest != HASH_REAVALIACAO_SERVICO or not ids or any(
            cid not in CAPTURAS_FALHA_SERVICO for cid in ids):
        raise ValueError("Reenvio de serviço fora da autorização de Luiz.")
    raiz = Path(__file__).resolve().parents[2]
    for cid in ids:
        caminho, sha, quantidade = CAPTURAS_FALHA_SERVICO[cid]
        conteudo = (raiz / caminho).read_bytes().replace(b"\r\n", b"\n")
        if hashlib.sha256(conteudo).hexdigest() != sha:
            raise ValueError(f"Captura de origem de {cid} foi alterada.")
        linhas = [json.loads(l) for l in conteudo.decode("utf-8").splitlines()]
        casos = [l for l in linhas if l.get("tipo") == "caso" and l.get("id") == cid]
        if (not linhas or linhas[0].get("hash_lote") != digest or len(casos) != 1 or
                casos[0].get("saida_provedor", object()) is not None or
                casos[0].get("classe_operacional") != "falha_servico" or
                (casos[0].get("erro_integracao") or {}).get("classe") not in
                {"ServerError", "ReadTimeout"}):
            raise ValueError(f"Contrato da captura de origem de {cid} inválido.")
        if (envios[cid] != quantidade or
                resultados.get(cid, {}).get("classe_operacional") != "falha_servico"):
            raise ValueError(f"Histórico de {cid} não autoriza novo reenvio.")


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


def configuracao_execucao(*, repetir_transitorios: bool = False) -> dict:
    if type(repetir_transitorios) is not bool:
        raise ValueError("Opção de repetição precisa ser booleana.")
    config = configuracao_geracao()
    return {**config, "politica_repeticao": politica_tentativas()} if repetir_transitorios else config


def _canonico(valor) -> str:
    return json.dumps(valor, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)


def hash_lote(manifesto: dict, *, repetir_transitorios: bool = False) -> str:
    validar_manifesto(manifesto)
    return hashlib.sha256(_canonico({"manifesto": manifesto, "configuracao":
                                   configuracao_execucao(repetir_transitorios=repetir_transitorios)}).encode("utf-8")).hexdigest()


def previa(manifesto: dict, *, repetir_transitorios: bool = False) -> dict:
    return {"tipo": "previa", "hash_lote": hash_lote(manifesto, repetir_transitorios=repetir_transitorios),
            "configuracao": configuracao_execucao(repetir_transitorios=repetir_transitorios),
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


def classificar_resultado(caso: dict, captura: dict, resposta: Resposta) -> str:
    """Classe operacional, sem inferir acerto factual nem causa de serviço."""
    if caso["id"] == "E20":
        return "controle_local"
    erro = captura["erro_integracao"]
    if erro is not None:
        if erro.get("fase") == "gerador" and (
                (erro.get("classe") in {"ServerError", "ClientError", "APIError"} and
                 erro.get("codigo") in CODIGOS_TRANSITORIOS) or
                erro.get("classe") in {"TimeoutException", "ReadTimeout", "ConnectTimeout",
                                       "NetworkError", "ConnectError", "RemoteProtocolError"}):
            return "falha_servico"
        return "falha_integracao"
    if resposta.status == "erro_geracao":
        saida = captura["saida_provedor"]
        return ("truncamento_observado" if isinstance(saida, dict) and
                saida.get("_erro_contrato") == "truncamento_observado" else "falha_contrato")
    return "recusa" if resposta.status == "sem_evidencia" else "respondida_pendente_julgamento"


def executar(manifesto: dict, *, aprovacao_sha256: str, previsao: int,
             saida: Path, gerar=None, repetir_transitorios: bool = False,
             previsao_falhas_contrato: int | None = None,
             ids_execucao: list[str] | None = None,
             registro_orcamento: Path | None = None,
             reavaliar_falhas_locais: bool = False,
             reavaliar_falha_servico: bool = False,
             limiar_contrato: int = LIMIAR_ABSOLUTO) -> None:
    # Cópia congelada impede alteração do lote durante a rodada.
    validar_manifesto(manifesto)
    manifesto = json.loads(_canonico(manifesto))
    digest = hash_lote(manifesto, repetir_transitorios=repetir_transitorios)
    if not isinstance(aprovacao_sha256, str) or aprovacao_sha256 != digest:
        raise ValueError("Hash de aprovação não corresponde ao lote.")
    if type(previsao) is not int or not 0 <= previsao <= 20:
        raise ValueError("Previsão deve ser inteiro entre 0 e 20.")
    if gerar is None and (type(previsao_falhas_contrato) is not int
                          or not 0 <= previsao_falhas_contrato <= 20):
        raise ValueError("Registre a previsão de falhas de contrato antes da API.")
    if type(limiar_contrato) is not int or not 1 <= limiar_contrato <= 5:
        raise ValueError("Limiar de contrato inválido.")
    if gerar is None and limiar_contrato != LIMIAR_ABSOLUTO:
        raise ValueError("A execução real exige o limiar absoluto aprovado de cinco falhas.")
    if ids_execucao is not None:
        permitidos = {c["id"] for c in manifesto["casos"]}
        if not isinstance(ids_execucao, list) or not ids_execucao or any(
                not isinstance(i, str) or i not in permitidos for i in ids_execucao
        ) or len(set(ids_execucao)) != len(ids_execucao):
            raise ValueError("IDs da execução inválidos.")
    selecionados = [c for c in manifesto["casos"]
                   if ids_execucao is None or c["id"] in ids_execucao]
    real = gerar is None
    if type(reavaliar_falhas_locais) is not bool or type(reavaliar_falha_servico) is not bool:
        raise ValueError("Opção de reavaliação precisa ser booleana.")
    if reavaliar_falhas_locais and reavaliar_falha_servico:
        raise ValueError("Opções de reavaliação incompatíveis.")
    if reavaliar_falhas_locais and (not real or digest != HASH_REAVALIACAO_LOCAL or
            not selecionados or any(c["id"] not in IDS_REAVALIACAO_LOCAL for c in selecionados)):
        raise ValueError("Reavaliação local fora da autorização de Luiz.")
    caminho_cota = (registro_orcamento or
                    Path(__file__).resolve().parents[2] / "data/demo/execucoes.jsonl")
    falhas_anteriores = 0
    pareadas_anteriores = 0
    pareaveis_concluidos = set()
    if real:
        from src.rag import liberacao
        historico = liberacao._ler_registro(caminho_cota)
        envios = Counter(l.get("id") for l in historico if l["tipo"] == "envio" and
                         l.get("origem") == "avaliacao" and l.get("hash") == digest)
        resultados = {l.get("id"): l for l in historico if l["tipo"] == "resultado" and
                      l.get("origem") == "avaliacao" and l.get("hash") == digest}
        if reavaliar_falha_servico:
            autorizar_reenvio_servico([c["id"] for c in selecionados], digest, envios, resultados)
        if reavaliar_falhas_locais:
            conteudo_captura = CAPTURA_FALHA_LOCAL.read_bytes()
            if hashlib.sha256(conteudo_captura).hexdigest() != SHA256_CAPTURA_FALHA_LOCAL:
                raise ValueError("Captura da falha local foi alterada.")
            captura = [json.loads(l) for l in conteudo_captura.decode("utf-8").splitlines()]
            if not captura or captura[0].get("hash_lote") != digest:
                raise ValueError("Captura da falha local não confere com o hash.")
            falhas_locais = {l.get("id") for l in captura if l.get("tipo") == "caso" and
                             (l.get("erro_integracao") or {}).get("classe") == "ConnectError" and
                             l.get("saida_provedor") is None}
            if any(envios[c["id"]] != 1 or
                   resultados.get(c["id"], {}).get("classe_operacional") != "falha_servico" or
                   c["id"] not in falhas_locais for c in selecionados):
                raise ValueError("Reavaliação exige uma única falha local anterior por caso.")
        elif not reavaliar_falha_servico and any(envios[c["id"]] for c in selecionados):
            raise ValueError("Casos já enviados sob este hash; selecione apenas IDs pendentes.")
        for linha in resultados.values():
            falha = linha.get("classe_operacional") in {"falha_contrato", "truncamento_observado"}
            falhas_anteriores += falha
            pareadas_anteriores += falha and linha.get("id") in IDS_PAREAVEIS_BASELINE
            if (linha.get("id") in IDS_PAREAVEIS_BASELINE and
                    linha.get("classe_operacional") not in {"falha_servico", "falha_integracao"}):
                pareaveis_concluidos.add(linha["id"])
        fase_pareavel_completa = pareaveis_concluidos == IDS_PAREAVEIS_BASELINE
        if (fase_pareavel_completa and pareadas_anteriores >= LIMIAR_PAREADO or
                fase_pareavel_completa and falhas_anteriores >= LIMIAR_ABSOLUTO):
            raise ValueError("Parada antecipada já atingida em execução anterior.")
        if (not fase_pareavel_completa and
                any(c["id"] not in IDS_PAREAVEIS_BASELINE for c in selecionados)):
            raise ValueError("Conclua os 13 casos pareáveis antes dos demais.")
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
        registrar({"tipo": "cabecalho", "hash_lote": digest,
                   "configuracao": configuracao_execucao(repetir_transitorios=repetir_transitorios),
                   "manifesto": manifesto, "previsao": previsao,
                   "previsao_falhas_contrato": previsao_falhas_contrato,
                   "limiar_contrato": limiar_contrato,
                   "limiar_pareado": LIMIAR_PAREADO,
                   "ids_pareaveis_baseline": sorted(IDS_PAREAVEIS_BASELINE),
                   "ids_execucao": [c["id"] for c in selecionados],
                   "reavaliacao_falha_local": reavaliar_falhas_locais,
                   "reavaliacao_falha_servico": reavaliar_falha_servico,
                   "captura_origem": "reports/geracao_citacao_afirmacao_fase1_20261019.jsonl"
                   if reavaliar_falhas_locais else None,
                   "falhas_contrato_anteriores": falhas_anteriores,
                   "falhas_pareadas_anteriores": pareadas_anteriores,
                   "utc": datetime.now(timezone.utc).isoformat()})
        try:
            if gerar is None:
                gerar, client = _criar_gerador()
            concluidos = 0
            falhas_contrato = falhas_anteriores
            falhas_pareadas = pareadas_anteriores
            for caso in selecionados:
                registro_cota = None
                if real and caso["id"] != "E20":
                    # Mesmo contador local do CLI; reserva duas chamadas por caso.
                    from src.rag import liberacao
                    agora = datetime.now(timezone.utc)
                    if liberacao.chamadas_no_dia(caminho_cota, agora) + 2 > liberacao.TETO_DIARIO:
                        registrar({"tipo": "cota_esgotada", "id": caso["id"], "utc": agora.isoformat()})
                        break
                    registro_cota = liberacao.Registro(
                        caminho_cota, f"lote-{digest[:12]}-{caso['id']}-{agora.strftime('%Y%m%dT%H%M%S%f')}",
                        lambda: datetime.now(timezone.utc))
                    registro_cota.envio({"hash": digest, "id": caso["id"], "origem": "avaliacao",
                                         "reavaliacao_falha_local": reavaliar_falhas_locais,
                                         "reavaliacao_falha_servico": reavaliar_falha_servico})
                captura = {"saida_provedor": None, "erro_integracao": None}
                falha_registro = []
                def registrar_tentativa(evento):
                    try:
                        registrar({"tipo": "tentativa", "id": caso["id"], **evento})
                    except Exception as erro:
                        falha_registro.append(erro)
                        raise
                gerar_caso = (GeradorComTentativas(gerar, registrar_tentativa)
                              if repetir_transitorios else gerar)
                def capturar(pergunta, evidencias):
                    try:
                        resultado = gerar_caso(pergunta, evidencias)
                        captura["saida_provedor"] = _saida_serializavel(resultado)
                        return resultado
                    except Exception as erro:
                        if not falha_registro:
                            captura["erro_integracao"] = _erro_seguro(erro, "gerador")
                        raise
                try:
                    resposta = responder(caso["pergunta"], caso["evidencias"], capturar)
                except Exception as erro:
                    captura["erro_integracao"] = _erro_seguro(erro, "validacao_aplicacao")
                    resposta = Resposta("erro_geracao", "Saída inválida do modelo.")
                if falha_registro:
                    # responder captura falhas do gerador; falha do registro encerra a rodada.
                    raise falha_registro[0]
                classe = classificar_resultado(caso, captura, resposta)
                registrar({"tipo": "caso", "id": caso["id"], **captura,
                           "resposta_aplicacao": asdict(resposta),
                           "classe_operacional": classe,
                           "status_esperado_compativel": resposta.status in caso["status_esperados"],
                           "julgamento_semantico": "pendente",
                           "tentativa": gerar_caso.tentativas if repetir_transitorios else 1})
                concluidos += 1
                if registro_cota is not None:
                    registro_cota.resultado({"tentativas": gerar_caso.tentativas if repetir_transitorios else 1,
                                            "status": resposta.status, "hash": digest,
                                            "id": caso["id"], "origem": "avaliacao",
                                            "classe_operacional": classe})
                falha_contrato = classe in {"falha_contrato", "truncamento_observado"}
                falhas_contrato += falha_contrato
                falhas_pareadas += falha_contrato and caso["id"] in IDS_PAREAVEIS_BASELINE
                if (caso["id"] in IDS_PAREAVEIS_BASELINE and
                        classe not in {"falha_servico", "falha_integracao"}):
                    pareaveis_concluidos.add(caso["id"])
                fase_pareavel_completa = pareaveis_concluidos == IDS_PAREAVEIS_BASELINE
                parada_pareada = fase_pareavel_completa and falhas_pareadas >= LIMIAR_PAREADO
                parada_total = (fase_pareavel_completa and falhas_contrato >= limiar_contrato)
                if (real or limiar_contrato != LIMIAR_ABSOLUTO) and (parada_pareada or parada_total):
                    registrar({"tipo": "parada_contrato", "id": caso["id"],
                               "falhas_contrato": falhas_contrato,
                               "falhas_pareadas": falhas_pareadas,
                               "limiar_absoluto": limiar_contrato,
                               "limiar_pareado": LIMIAR_PAREADO})
                    break
            registrar({"tipo": "fim", "casos_registrados": concluidos,
                       "casos_selecionados": len(selecionados),
                       "falhas_contrato": falhas_contrato,
                       "falhas_pareadas": falhas_pareadas,
                       "lote_completo": concluidos == len(selecionados)})
        finally:
            if client is not None:
                client.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifesto", required=True, type=Path)
    parser.add_argument("--executar", action="store_true")
    parser.add_argument("--repetir-transitorios", action="store_true")
    parser.add_argument("--aprovacao-sha256")
    parser.add_argument("--previsao", type=int)
    parser.add_argument("--previsao-falhas-contrato", type=int)
    parser.add_argument("--ids", help="IDs E01–E20 separados por vírgula para repartir dias de cota")
    parser.add_argument("--reavaliar-falhas-locais", action="store_true")
    parser.add_argument("--reavaliar-falha-servico", action="store_true")
    parser.add_argument("--saida", type=Path)
    argumentos = parser.parse_args(argv)
    try:
        manifesto = carregar_manifesto(argumentos.manifesto)
        if argumentos.executar:
            if argumentos.saida is None:
                raise ValueError("Informe saída nova para executar.")
            executar(manifesto, aprovacao_sha256=argumentos.aprovacao_sha256,
                     previsao=argumentos.previsao, saida=argumentos.saida,
                     repetir_transitorios=argumentos.repetir_transitorios,
                     previsao_falhas_contrato=argumentos.previsao_falhas_contrato,
                     ids_execucao=argumentos.ids.split(",") if argumentos.ids else None,
                     reavaliar_falhas_locais=argumentos.reavaliar_falhas_locais,
                     reavaliar_falha_servico=argumentos.reavaliar_falha_servico)
        else:
            print(json.dumps(previa(manifesto, repetir_transitorios=argumentos.repetir_transitorios),
                             ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError) as erro:
        if argumentos.reavaliar_falha_servico:
            print(f"Falha: {erro}", file=sys.stderr)
        else:
            print("Falha: confira contrato, aprovação, previsão e arquivo de saída.", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
