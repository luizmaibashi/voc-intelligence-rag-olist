"""Contagem descritiva de atraso entre avaliações com comentário e entrega."""
from dataclasses import dataclass
from math import sqrt

import pandas as pd


@dataclass(frozen=True)
class FrequenciaAtrasos:
    atrasadas: int
    entregues: int
    proporcao: float
    ic95_inf: float
    ic95_sup: float
    inicio: str
    fim: str

    @property
    def resumo(self) -> str:
        return (
            f"Entregas atrasadas: {self.atrasadas} de {self.entregues} avaliações "
            f"com comentário de pedidos entregues ({self.proporcao:.1%}; "
            f"IC95% de Wilson: {self.ic95_inf:.1%}–{self.ic95_sup:.1%}). "
            f"Compras de {self.inicio} a {self.fim}."
        )


def _intervalo_wilson(acertos: int, total: int) -> tuple[float, float]:
    z = 1.96
    p = acertos / total
    base = 1 + z * z / total
    centro = (p + z * z / (2 * total)) / base
    margem = z * sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / base
    return centro - margem, centro + margem


def contar_atrasos(corpus: pd.DataFrame) -> FrequenciaAtrasos:
    """Conta `review_id` no corpus processado; não estima todos os pedidos."""
    colunas = {"review_id", "texto", "situacao_entrega", "data_compra"}
    if not isinstance(corpus, pd.DataFrame) or not colunas.issubset(corpus.columns):
        raise ValueError("Corpus precisa de review_id, texto, situacao_entrega e data_compra.")
    if corpus.texto.isna().any() or not corpus.texto.map(
        lambda v: isinstance(v, str) and bool(v.strip())
    ).all():
        raise ValueError("Corpus contém avaliação sem comentário.")
    ids = corpus.review_id
    if ids.isna().any() or not ids.map(lambda v: isinstance(v, str) and bool(v.strip())).all():
        raise ValueError("review_id ausente ou inválido.")
    if ids.duplicated().any():
        raise ValueError("review_id duplicado: a unidade de contagem não está definida.")
    estados = {"atrasado", "no_prazo", "nao_entregue"}
    if not corpus.situacao_entrega.isin(estados).all():
        raise ValueError("situacao_entrega desconhecida ou ausente.")

    elegiveis = corpus.loc[corpus.situacao_entrega.isin({"atrasado", "no_prazo"})]
    total = len(elegiveis)
    if total == 0:
        raise ValueError("Não há pedidos entregues com comentário no recorte.")
    datas = pd.to_datetime(elegiveis.data_compra, errors="coerce")
    if datas.isna().any():
        raise ValueError("data_compra inválida em pedido entregue.")

    atrasadas = int(elegiveis.situacao_entrega.eq("atrasado").sum())
    inf, sup = _intervalo_wilson(atrasadas, total)
    return FrequenciaAtrasos(
        atrasadas=atrasadas,
        entregues=total,
        proporcao=atrasadas / total,
        ic95_inf=inf,
        ic95_sup=sup,
        inicio=datas.min().date().isoformat(),
        fim=datas.max().date().isoformat(),
    )
