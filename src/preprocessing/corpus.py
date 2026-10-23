"""Monta o corpus do RAG: uma linha por avaliação com texto, mais os metadados de filtro.

Limpeza mínima de propósito: stopwords, negação, acento e caixa ficam, porque o modelo de
embedding usa a frase inteira (ver reports/eda_olist.md e docs/adr quando existir).
"""
import re
from pathlib import Path

import pandas as pd

AUSENCIA_MASCARADA = {".", "-", "..", "...", "ok", "nada", "x", "a", "sim", "não", "nao"}


def montar_texto(titulo, mensagem) -> str:
    partes = [re.sub(r"\s+", " ", str(p)).strip() for p in (titulo, mensagem) if pd.notna(p)]
    partes = [p for p in partes if p]
    if len(partes) == 2 and partes[0][-1] not in ".!?":
        partes[0] += "."
    return " ".join(partes)


def eh_ausencia_mascarada(texto: str) -> bool:
    return texto.strip().lower() in AUSENCIA_MASCARADA


def _situacao_entrega(pedidos: pd.DataFrame) -> pd.Series:
    entregue = pedidos.order_delivered_customer_date.notna()
    atrasado = (pedidos.order_delivered_customer_date.dt.normalize()
                > pedidos.order_estimated_delivery_date.dt.normalize())
    return pd.Series("no_prazo", index=pedidos.index).mask(atrasado, "atrasado").mask(~entregue, "nao_entregue")


def _categorias_por_pedido(items: pd.DataFrame, products: pd.DataFrame) -> pd.Series:
    cat = items.merge(products[["product_id", "product_category_name"]], on="product_id", how="left")
    cat = cat.dropna(subset=["product_category_name"])
    return cat.groupby("order_id").product_category_name.agg(lambda s: "|".join(sorted(set(s))))


def montar_corpus(reviews: pd.DataFrame, orders: pd.DataFrame, items: pd.DataFrame,
                  products: pd.DataFrame) -> pd.DataFrame:
    df = reviews.drop_duplicates("review_id", keep="first").copy()
    df["texto"] = [montar_texto(t, m) for t, m in zip(df.review_comment_title, df.review_comment_message)]
    df = df[df.texto.ne("") & ~df.texto.map(eh_ausencia_mascarada)]

    df = df.merge(orders, on="order_id", how="left", validate="many_to_one")
    df["situacao_entrega"] = _situacao_entrega(df)
    df["dias_atraso"] = (df.order_delivered_customer_date - df.order_estimated_delivery_date).dt.days
    df["categorias"] = df.order_id.map(_categorias_por_pedido(items, products)).fillna("sem_categoria")
    chave = df.texto.str.lower()
    df["freq_texto"] = chave.map(chave.value_counts())

    return df[["review_id", "order_id", "texto", "review_score", "review_creation_date",
               "order_purchase_timestamp", "order_status", "situacao_entrega", "dias_atraso",
               "categorias", "freq_texto"]].rename(columns={"review_score": "nota",
                                                           "review_creation_date": "data_avaliacao",
                                                           "order_purchase_timestamp": "data_compra"})


def main() -> None:
    raiz = Path(__file__).resolve().parents[2]
    raw = raiz / "data/raw"
    datas_r = ["review_creation_date"]
    datas_o = ["order_purchase_timestamp", "order_delivered_customer_date", "order_estimated_delivery_date"]
    reviews = pd.read_csv(raw / "olist_order_reviews_dataset.csv", parse_dates=datas_r)
    orders = pd.read_csv(raw / "olist_orders_dataset.csv", parse_dates=datas_o)
    items = pd.read_csv(raw / "olist_order_items_dataset.csv", usecols=["order_id", "product_id"])
    products = pd.read_csv(raw / "olist_products_dataset.csv", usecols=["product_id", "product_category_name"])

    corpus = montar_corpus(reviews, orders, items, products)
    saida = raiz / "data/processed/corpus_reviews.parquet"
    saida.parent.mkdir(parents=True, exist_ok=True)
    corpus.to_parquet(saida, index=False)
    print(f"entrada: {reviews.review_id.nunique()} review_id únicos -> corpus: {len(corpus)} documentos")
    print(corpus.situacao_entrega.value_counts().to_dict())
    print(f"textos distintos: {corpus.texto.str.lower().nunique()}")


if __name__ == "__main__":
    main()
