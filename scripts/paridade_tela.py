"""Confere os hashes liberados sem criar cliente Gemini."""

from src.demo import (CACHE_VETORES, RAIZ, REGISTRO_PADRAO, carregar_corpus,
                      carregar_modelo, responder_cli)
from src.tela.logica import argumentos_responder

CASOS = (
    ("E-A", "O que os clientes relatam sobre entregas atrasadas?", "28fb0e20214f31f163156580e6a1f3fddfcd18c6fa71fc890e5a607506b40a88"),
    ("E-B", "O que os clientes relatam que aconteceu depois que a entrega atrasou?", "72ea2402264ac2f80a6a7c3ea043a10de4b72209b6eddb07f53b2c1435bf68ec"),
    ("P15", "Qual é o prazo oficial de reembolso da Olist quando uma entrega atrasa?", "c53daa6570b52c72f4a9b289b7ae87d21be989beac77b7af34f9c729a8684e24"),
)


def main() -> int:
    corpus = carregar_corpus(RAIZ / "data/processed/corpus_reviews.parquet")
    modelo = carregar_modelo()
    falhas = 0
    for nome, pergunta, esperado in CASOS:
        args = argumentos_responder(pergunta, 10, None, 2, "atrasado", None, None, None)
        saida = responder_cli(corpus, modelo=modelo, **args, executar=False,
                              registro=REGISTRO_PADRAO, cache_vetores=CACHE_VETORES)
        ok = saida.get("hash") == esperado
        print(f"{nome}: {'ok' if ok else 'DIVERGE'}")
        falhas += not ok
    return int(bool(falhas))


if __name__ == "__main__":
    raise SystemExit(main())
