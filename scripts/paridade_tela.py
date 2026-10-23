"""Confere os hashes liberados sem criar cliente Gemini."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.demo import (CACHE_VETORES, RAIZ, REGISTRO_PADRAO, carregar_corpus,
                      carregar_modelo, responder_cli)
from src.tela.logica import PERGUNTAS_DEMO, argumentos_responder


def main() -> int:
    corpus = carregar_corpus(RAIZ / "data/processed/corpus_reviews.parquet")
    modelo = carregar_modelo()
    falhas = 0
    for caso in PERGUNTAS_DEMO:
        args = argumentos_responder(caso["pergunta"], caso["k"], caso["nota_min"],
                                    caso["nota_max"], caso["situacao"], caso["categoria"],
                                    caso["compra_de"], caso["compra_ate"])
        saida = responder_cli(corpus, modelo=modelo, **args, executar=False,
                              registro=REGISTRO_PADRAO, cache_vetores=CACHE_VETORES)
        ok = saida.get("hash") == caso["hash"]
        print(f"{caso['id']}: {'ok' if ok else 'DIVERGE'}")
        falhas += not ok
    return int(bool(falhas))


if __name__ == "__main__":
    raise SystemExit(main())
