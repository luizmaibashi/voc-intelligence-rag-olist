"""Busca/fontes/contagem locais, ensaio sintético e resposta gerada com prévia e hash.

Só `--acao responder --executar --aprovacao-sha256 <hash>` chama o Gemini (spec 0007).
"""
import argparse
import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd
from sentence_transformers import SentenceTransformer

from src.analytics.frequencia import contar_atrasos
from src.rag import liberacao
from src.rag.responder import responder
from src.rag.tentativas import GeradorComTentativas
from src.retrieval.cache import vetores_com_cache
from src.retrieval.indice import (DIM, MODELO, buscar, carregar_corpus,
                                  codificar_pergunta, criar_indice, gerar_vetores)

RAIZ = Path(__file__).resolve().parents[1]
REGISTRO_PADRAO = RAIZ / "data/demo/execucoes.jsonl"
# Vetores de todas as linhas do corpus, em ordem; nunca o cache distinto do pooling (spec 0010).
CACHE_VETORES = RAIZ / "data/processed/emb_busca_minilm.npy"
PERGUNTA_ATRASOS = "O que os clientes relatam sobre entregas atrasadas?"
PERGUNTA_POLITICA = "Qual é o prazo oficial de reembolso da Olist quando uma entrega atrasa?"
LIMITES = ("Avaliações históricas com comentário; não representa todos os pedidos "
           "nem a operação atual. IC95% não corrige a autosseleção de quem comenta.")


def carregar_modelo():
    # Pesos devem estar disponíveis antes da execução; nenhum download implícito.
    return SentenceTransformer(MODELO, local_files_only=True)


def quantificar(corpus: pd.DataFrame) -> dict:
    resultado = contar_atrasos(corpus)
    return {"modo": "contagem_local", "resultado": asdict(resultado),
            "resumo": resultado.resumo, "limites": LIMITES,
            "gate_demo": "bloqueado"}


def recuperar(corpus: pd.DataFrame, pergunta: str, modelo, *, k: int = 10,
              nota_min=None, nota_max=None, situacao_entrega=None,
              cache_vetores: Path | None = None) -> dict:
    if not isinstance(pergunta, str) or not pergunta.strip():
        raise ValueError("Informe uma pergunta não vazia.")
    colunas = {"review_id", "texto", "nota", "situacao_entrega", "categorias"}
    if not isinstance(corpus, pd.DataFrame) or not colunas.issubset(corpus.columns):
        raise ValueError("Corpus sem as colunas da busca.")
    if corpus.empty or not corpus.texto.map(
            lambda v: isinstance(v, str) and bool(v.strip())).all():
        raise ValueError("Corpus vazio ou comentário inválido.")
    # Índice efêmero preserva todas as linhas; filtros/deduplicação vivem em buscar.
    if cache_vetores is None:
        vetores = gerar_vetores(corpus, modelo)
    else:
        vetores = vetores_com_cache(cache_vetores, modelo, corpus.texto.tolist(),
                                    nome_modelo=MODELO, dimensao=DIM)
    with duckdb.connect() as con:
        criar_indice(con, corpus, vetores)
        achados = buscar(con, codificar_pergunta(modelo, pergunta), k=k,
                         nota_min=nota_min, nota_max=nota_max,
                         situacao_entrega=situacao_entrega)
    return {"modo": "busca_local_sem_geracao", "pergunta": pergunta,
            "modelo_embedding": MODELO,
            "filtros": {"k": k, "nota_min": nota_min, "nota_max": nota_max,
                        "situacao_entrega": situacao_entrega},
            "fontes": achados.to_dict("records"),
            "aviso": "Resultados são evidências candidatas, não uma resposta nem frequência temática.",
            "gate_demo": "bloqueado"}


def corpus_sintetico() -> pd.DataFrame:
    return pd.DataFrame({
        "review_id": ["sintetico-01", "sintetico-02", "sintetico-03"],
        "texto": ["A entrega atrasou três dias. A caixa chegou intacta.",
                  "A entrega atrasou cinco dias e a caixa chegou amassada.",
                  "Chegou no prazo, com a embalagem intacta."],
        "nota": [2, 1, 5],
        "situacao_entrega": ["atrasado", "atrasado", "no_prazo"],
        "categorias": ["sintetica"] * 3,
        "data_compra": pd.to_datetime(["2018-01-01", "2018-02-01", "2018-03-01"]),
    })


def ensaio_sintetico(modelo) -> dict:
    corpus = corpus_sintetico()
    consultas = []
    # Gerador falso só é definido dentro do ensaio e só recebe dados inventados.
    def gerar_falso(pergunta, evidencias):
        if pergunta == PERGUNTA_POLITICA:
            return {"status": "sem_evidencia",
                    "texto": "Os relatos inventados não estabelecem política oficial.",
                    "review_ids": []}
        return {"status": "respondida",
                "texto": "Relatos da simulação: " + " ".join(e["texto"] for e in evidencias),
                "review_ids": [e["review_id"] for e in evidencias]}
    for pergunta in (PERGUNTA_ATRASOS, PERGUNTA_POLITICA):
        busca = recuperar(corpus, pergunta, modelo, k=2, nota_max=2,
                          situacao_entrega="atrasado")
        evidencias = [{"review_id": f["review_id"], "texto": f["texto"]}
                      for f in busca["fontes"]]
        resposta = responder(pergunta, evidencias, gerar_falso)
        consultas.append({**busca, "modo": "simulacao_sintetica",
                          "resposta_simulada": asdict(resposta),
                          "fontes_citadas": [f for f in busca["fontes"]
                                             if f["review_id"] in resposta.review_ids]})
    return {"modo": "simulacao_sintetica", "gerador": "falso_local",
            "aviso": "Somente dados inventados; verifica integração, não qualidade ou disponibilidade do Gemini.",
            "consultas": consultas, "contagem": quantificar(corpus),
            "gate_demo": "bloqueado"}


def _criar_gerador():
    # Import tardio: prévia e testes nunca constroem cliente nem leem credencial.
    from src.eval.avaliar_geracao import _criar_gerador as criar
    return criar()


def _gerar_simulado(pergunta, evidencias):
    return {"status": "respondida",
            "texto": "Resposta simulada a partir de: " + " ".join(e["texto"] for e in evidencias),
            "review_ids": [e["review_id"] for e in evidencias]}


def responder_cli(corpus: pd.DataFrame, pergunta: str, modelo, *, k: int = 10,
                  nota_min=None, nota_max=None, situacao_entrega=None,
                  executar: bool = False, aprovacao_sha256=None, gerador: str = "gemini",
                  registro: Path = REGISTRO_PADRAO, agora: datetime | None = None,
                  criar_gerador=None, cache_vetores: Path | None = None) -> dict:
    """Prévia sem API por padrão; envio só com hash idêntico e orçamento disponível."""
    if gerador not in {"gemini", "falso"}:
        raise ValueError("Gerador deve ser gemini ou falso.")
    busca = recuperar(corpus, pergunta, modelo, k=k, nota_min=nota_min,
                      nota_max=nota_max, situacao_entrega=situacao_entrega,
                      cache_vetores=cache_vetores)
    evidencias = [{"review_id": f["review_id"], "texto": f["texto"]} for f in busca["fontes"]]
    base = {"pergunta": pergunta, "modelo_embedding": MODELO, "filtros": busca["filtros"],
            "contexto": busca["fontes"], "limites": LIMITES}

    def com_resposta(modo: str, resposta) -> dict:
        citadas = [f for f in busca["fontes"] if f["review_id"] in resposta.review_ids]
        return {**base, "modo": modo, "resposta": asdict(resposta), "fontes_citadas": citadas,
                "aviso": "Citação válida não prova que cada frase tem suporte; confira as fontes."}

    if gerador == "falso":
        return com_resposta("simulado", responder(pergunta, evidencias, _gerar_simulado))

    relogio = (lambda: agora) if agora is not None else (lambda: datetime.now(timezone.utc))
    payload = liberacao.montar_payload(pergunta, busca["filtros"], evidencias)
    digest = liberacao.hash_payload(payload)
    if not executar:
        return {**base, "modo": "previa_sem_api", "hash": digest,
                "alertas_pii": liberacao.alertas_pii(pergunta, evidencias),
                "chamadas_restantes_hoje": liberacao.restantes_hoje(registro, relogio()),
                "proximo_passo": ("Leia o contexto acima. Se nada identificar o cliente, repita o "
                                  f"comando com --executar --aprovacao-sha256 {digest}"),
                "aviso": "Nada foi enviado. Alerta de PII é heurístico e não substitui a leitura."}

    liberacao.exigir_liberacao(digest, aprovacao_sha256, registro, relogio())
    gerar, cliente = (criar_gerador or _criar_gerador)()
    reg = liberacao.Registro(registro, f"{digest[:12]}-{relogio().strftime('%Y%m%dT%H%M%S')}", relogio)
    reg.envio({"hash": digest, "pergunta": pergunta, "filtros": busca["filtros"],
               "ids_contexto": [e["review_id"] for e in evidencias],
               "codigo": payload["codigo"]})
    com_tentativas = GeradorComTentativas(gerar, reg.tentativa)
    try:
        resposta = responder(pergunta, evidencias, com_tentativas)
    finally:
        if cliente is not None:
            cliente.close()
    reg.resultado({"status": resposta.status, "texto": resposta.texto,
                   "review_ids": resposta.review_ids, "tentativas": com_tentativas.tentativas})
    return {**com_resposta("geracao_real", resposta), "hash": digest,
            "tentativas": com_tentativas.tentativas,
            "chamadas_restantes_hoje": liberacao.restantes_hoje(registro, relogio())}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acao", choices=["buscar", "responder", "contar", "ensaio-sintetico"],
                        default="ensaio-sintetico")
    parser.add_argument("--executar", action="store_true",
                        help="Envia ao Gemini; exige o hash impresso pela prévia.")
    parser.add_argument("--aprovacao-sha256")
    parser.add_argument("--gerador", choices=["gemini", "falso"], default="gemini")
    parser.add_argument("--corpus", type=Path,
                        default=RAIZ / "data/processed/corpus_reviews.parquet")
    parser.add_argument("--pergunta")
    parser.add_argument("--k", type=int, default=10)
    parser.add_argument("--nota-min", type=int)
    parser.add_argument("--nota-max", type=int)
    parser.add_argument("--situacao-entrega", choices=["atrasado", "no_prazo", "nao_entregue"])
    args = parser.parse_args(argv)
    filtros_informados = any(v is not None for v in
                            (args.nota_min, args.nota_max, args.situacao_entrega))
    com_pergunta = {"buscar", "responder"}
    if args.acao not in com_pergunta and (args.pergunta is not None or filtros_informados or args.k != 10):
        parser.error("Pergunta/filtros/k só se aplicam às ações buscar e responder.")
    if args.acao in com_pergunta and (not args.pergunta or not args.pergunta.strip()):
        parser.error(f"A ação {args.acao} exige --pergunta não vazia.")
    if args.acao != "responder" and (args.executar or args.aprovacao_sha256 or args.gerador != "gemini"):
        parser.error("--executar, --aprovacao-sha256 e --gerador só se aplicam à ação responder.")
    if args.executar and args.gerador == "falso":
        parser.error("O gerador falso não envia nada; dispensa --executar.")
    try:
        if args.acao == "ensaio-sintetico":
            saida = ensaio_sintetico(carregar_modelo())
        elif args.acao == "contar":
            saida = quantificar(carregar_corpus(args.corpus))
        elif args.acao == "responder":
            saida = responder_cli(carregar_corpus(args.corpus), args.pergunta, carregar_modelo(),
                                  k=args.k, nota_min=args.nota_min, nota_max=args.nota_max,
                                  situacao_entrega=args.situacao_entrega, executar=args.executar,
                                  aprovacao_sha256=args.aprovacao_sha256, gerador=args.gerador,
                                  registro=REGISTRO_PADRAO, criar_gerador=_criar_gerador,
                                  cache_vetores=CACHE_VETORES)
        else:
            saida = recuperar(carregar_corpus(args.corpus), args.pergunta, carregar_modelo(),
                              k=args.k, nota_min=args.nota_min, nota_max=args.nota_max,
                              situacao_entrega=args.situacao_entrega,
                              cache_vetores=CACHE_VETORES)
        print(json.dumps(saida, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except liberacao.EnvioBloqueado as erro:
        print(f"Envio bloqueado: {erro}. Nenhuma API de geração chamada.", file=sys.stderr)
        return 3
    except (OSError, ValueError, KeyError, TypeError, duckdb.Error):
        print("Falha local: confira corpus, entrada, pesos MiniLM e credencial. Com --executar, "
              "confira em data/demo/execucoes.jsonl se houve chamada.",
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
