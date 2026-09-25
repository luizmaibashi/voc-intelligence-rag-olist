"""EDA das avaliações da Olist: os 9 itens do gate CRISP-DM + perfil do texto.

Gera reports/eda_olist.md. Rodar da raiz do projeto: python src/eda/01_eda_reviews.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.stats.proportion import proportion_confint

RAIZ = Path(__file__).resolve().parents[2]
RAW = RAIZ / "data/raw"
SAIDA = RAIZ / "reports/eda_olist.md"
AUSENCIA_MASCARADA = {".", "-", "..", "...", "ok", "nada", "x", "a", "sim", "não", "nao"}


def br(s: str) -> str:
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def pct(k: int, n: int) -> str:
    lo, hi = proportion_confint(k, n, method="wilson")
    return br(f"{k:,} de {n:,} ({k / n:.1%}; IC95% {lo:.1%} a {hi:.1%})")


def media_ic(s: pd.Series) -> str:
    m, se = s.mean(), s.std() / np.sqrt(len(s))
    return br(f"{m:.2f} (n={len(s):,}; IC95% {m - 1.96 * se:.2f} a {m + 1.96 * se:.2f})")


def carregar() -> pd.DataFrame:
    r = pd.read_csv(RAW / "olist_order_reviews_dataset.csv",
                    parse_dates=["review_creation_date", "review_answer_timestamp"])
    o = pd.read_csv(RAW / "olist_orders_dataset.csv",
                    parse_dates=["order_purchase_timestamp", "order_delivered_customer_date",
                                 "order_estimated_delivery_date"])
    return r.merge(o, on="order_id", how="left", validate="many_to_one")


def main() -> None:
    df = carregar()
    n = len(df)
    msg = df.review_comment_message.fillna("").str.strip()
    tem_texto = msg.ne("")
    linhas = [f"# EDA: avaliações Olist\n\nGerado por `src/eda/01_eda_reviews.py`. n = {n:,} avaliações.\n"
              .replace(",", ".")]

    linhas.append("## 1. Duplicatas\n")
    linhas.append(f"- `review_id` repetido: {pct(int(df.review_id.duplicated().sum()), n)}")
    linhas.append(f"- Linha inteira repetida: {int(df.duplicated().sum())}")
    linhas.append(f"- `order_id` com mais de uma avaliação: {pct(int(df.order_id.duplicated().sum()), n)}")
    rep = df[df.review_id.duplicated(keep=False)].groupby("review_id")
    mesma_msg = int(rep.review_comment_message.nunique(dropna=False).eq(1).sum())
    linhas.append(f"- Dos `review_id` repetidos, com a mesma mensagem em todas as cópias: "
                  f"{mesma_msg} de {rep.ngroups}")
    txt_rep = msg[tem_texto].str.lower().value_counts()
    linhas.append(f"- Textos idênticos (entre avaliações com texto): {pct(int((txt_rep[txt_rep > 1]).sum()), int(tem_texto.sum()))}")
    linhas.append("- 10 textos mais repetidos:\n")
    linhas += [f"  - `{t[:60]}`: {c}" for t, c in txt_rep.head(10).items()]

    linhas.append("\n## 2. Colunas constantes\n")
    const = [c for c in df.columns if df[c].nunique(dropna=False) <= 1]
    linhas.append(f"- {const or 'nenhuma'}")

    linhas.append("\n## 3. Sentinelas\n")
    fora = int((~df.review_score.between(1, 5)).sum())
    linhas.append(f"- `review_score` fora de 1 a 5: {fora}")
    linhas.append(f"- Distribuição de nota: {df.review_score.value_counts().sort_index().to_dict()}")

    linhas.append("\n## 4. Ausência mascarada no texto\n")
    masc = msg[tem_texto].str.lower().isin(AUSENCIA_MASCARADA)
    linhas.append(f"- Textos que são só `{sorted(AUSENCIA_MASCARADA)}`: {pct(int(masc.sum()), int(tem_texto.sum()))}")
    palavras = msg[tem_texto].str.split().str.len()
    linhas.append(f"- Comentários com 1 ou 2 palavras: {pct(int((palavras <= 2).sum()), int(tem_texto.sum()))}")

    linhas.append("\n## 5. Outliers relacionais\n")
    resp_antes = int((df.review_answer_timestamp < df.review_creation_date).sum())
    aval_antes = int((df.review_creation_date < df.order_purchase_timestamp.dt.normalize()).sum())
    linhas.append(f"- Resposta registrada antes da criação da avaliação: {resp_antes}")
    linhas.append(f"- Avaliação criada antes da compra: {pct(aval_antes, n)}")

    linhas.append("\n## 6. Nulos por coluna\n")
    linhas += [f"- `{c}`: {pct(int(k), n)}" for c, k in df.isna().sum().items() if k]

    linhas.append("\n## 7. Redundância\n")
    tit = df.review_comment_title.fillna("").str.strip()
    linhas.append(f"- Tem título: {pct(int(tit.ne('').sum()), n)}; "
                  f"tem título e não tem mensagem: {int((tit.ne('') & ~tem_texto).sum())}")

    linhas.append("\n## 8. Relação com a nota\n")
    entregue = df.order_delivered_customer_date.notna()
    atraso = df.order_delivered_customer_date > df.order_estimated_delivery_date
    linhas.append(f"- Nota média, entregue no prazo: {media_ic(df.loc[entregue & ~atraso, 'review_score'])}")
    linhas.append(f"- Nota média, entregue com atraso: {media_ic(df.loc[entregue & atraso, 'review_score'])}")
    linhas.append(f"- Nota média, não entregue: {media_ic(df.loc[~entregue, 'review_score'])}")
    linhas.append(f"- Status do pedido entre notas 1: {df.loc[df.review_score == 1, 'order_status'].value_counts().head(5).to_dict()}")

    linhas.append("\n## 9. A ausência de texto prevê a nota?\n")
    linhas.append(f"- Nota média com texto: {media_ic(df.loc[tem_texto, 'review_score'])}")
    linhas.append(f"- Nota média sem texto: {media_ic(df.loc[~tem_texto, 'review_score'])}")
    for s in range(1, 6):
        g = df.review_score == s
        linhas.append(f"- Nota {s}, escreveu comentário: {pct(int((g & tem_texto).sum()), int(g.sum()))}")

    linhas.append("\n## Perfil do texto (avaliações com comentário)\n")
    q = palavras.quantile([0.1, 0.5, 0.9]).astype(int).to_dict()
    linhas.append(f"- Palavras por comentário: p10={q[0.1]}, mediana={q[0.5]}, p90={q[0.9]}, máx={int(palavras.max())}")
    linhas.append(f"- Com quebra de linha dentro do texto: {pct(int(msg[tem_texto].str.contains(chr(10)).sum()), int(tem_texto.sum()))}")

    SAIDA.parent.mkdir(exist_ok=True)
    SAIDA.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print(f"ok: {SAIDA}")


if __name__ == "__main__":
    main()
