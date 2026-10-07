"""Busca/fontes/contagem locais e ensaio sintético. Não chama API de geração."""
import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

import duckdb
import pandas as pd
from sentence_transformers import SentenceTransformer

from src.analytics.frequencia import contar_atrasos
from src.rag.responder import responder
from src.retrieval.indice import (MODELO, buscar, carregar_corpus,
                                  codificar_pergunta, criar_indice, gerar_vetores)

RAIZ = Path(__file__).resolve().parents[1]
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
              nota_min=None, nota_max=None, situacao_entrega=None) -> dict:
    if not isinstance(pergunta, str) or not pergunta.strip():
        raise ValueError("Informe uma pergunta não vazia.")
    colunas = {"review_id", "texto", "nota", "situacao_entrega", "categorias"}
    if not isinstance(corpus, pd.DataFrame) or not colunas.issubset(corpus.columns):
        raise ValueError("Corpus sem as colunas da busca.")
    if corpus.empty or not corpus.texto.map(
            lambda v: isinstance(v, str) and bool(v.strip())).all():
        raise ValueError("Corpus vazio ou comentário inválido.")
    # Índice efêmero preserva todas as linhas; filtros/deduplicação vivem em buscar.
    vetores = gerar_vetores(corpus, modelo)
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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--acao", choices=["buscar", "contar", "ensaio-sintetico"],
                        default="ensaio-sintetico")
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
    if args.acao != "buscar" and (args.pergunta is not None or filtros_informados or args.k != 10):
        parser.error("Pergunta/filtros/k só se aplicam à ação buscar.")
    if args.acao == "buscar" and (not args.pergunta or not args.pergunta.strip()):
        parser.error("A ação buscar exige --pergunta não vazia.")
    try:
        if args.acao == "ensaio-sintetico":
            saida = ensaio_sintetico(carregar_modelo())
        elif args.acao == "contar":
            saida = quantificar(carregar_corpus(args.corpus))
        else:
            saida = recuperar(carregar_corpus(args.corpus), args.pergunta, carregar_modelo(),
                              k=args.k, nota_min=args.nota_min, nota_max=args.nota_max,
                              situacao_entrega=args.situacao_entrega)
        print(json.dumps(saida, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError, duckdb.Error):
        print("Falha local: confira corpus, entrada e pesos MiniLM disponíveis. Nenhuma API de geração chamada.",
              file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
