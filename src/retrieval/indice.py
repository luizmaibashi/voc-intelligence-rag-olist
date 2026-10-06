"""Busca exata com vetores normalizados e filtros de metadados em DuckDB."""
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

MODELO = "paraphrase-multilingual-MiniLM-L12-v2"
DIM = 384


def criar_indice(con: duckdb.DuckDBPyConnection, docs: pd.DataFrame,
                 vetores: np.ndarray) -> None:
    if len(docs) != len(vetores) or vetores.shape != (len(docs), DIM):
        raise ValueError("vetores e documentos incompatíveis")
    if docs.review_id.duplicated().any():
        raise ValueError("review_id duplicado")
    if not np.isfinite(vetores).all() or not np.allclose(np.linalg.norm(vetores, axis=1), 1, atol=1e-4):
        raise ValueError("vetores devem ser finitos e normalizados")
    colunas = ["review_id", "texto", "nota", "situacao_entrega", "categorias"]
    tabela = docs[colunas].copy()
    tabela["vetor"] = list(vetores.astype(np.float32))
    con.register("entrada_indice", tabela)
    try:
        con.execute(f"CREATE OR REPLACE TABLE avaliacoes AS SELECT review_id, texto, nota, "
                    f"situacao_entrega, categorias, vetor::FLOAT[{DIM}] AS vetor FROM entrada_indice")
    finally:
        con.unregister("entrada_indice")


def buscar(con: duckdb.DuckDBPyConnection, vetor: np.ndarray, k: int = 10,
           nota_min: int | None = None, nota_max: int | None = None,
           situacao_entrega: str | None = None) -> pd.DataFrame:
    vetor = np.asarray(vetor, dtype=np.float32)
    if vetor.shape != (DIM,) or not np.isfinite(vetor).all() or not np.isclose(np.linalg.norm(vetor), 1, atol=1e-4):
        raise ValueError("pergunta deve ter vetor normalizado de 384 dimensões")
    if (type(k) is not int or k < 1
            or (nota_min is not None and (type(nota_min) is not int or not 1 <= nota_min <= 5))
            or (nota_max is not None and (type(nota_max) is not int or not 1 <= nota_max <= 5))
            or (nota_min is not None and nota_max is not None and nota_min > nota_max)):
        raise ValueError("k ou intervalo de nota inválido")
    if situacao_entrega is not None and (not isinstance(situacao_entrega, str)
            or situacao_entrega not in {"atrasado", "no_prazo", "nao_entregue"}):
        raise ValueError("situação de entrega inválida")
    sql = f"""SELECT review_id, texto, nota, situacao_entrega,
                     array_cosine_similarity(vetor, ?::FLOAT[{DIM}]) AS score
              FROM avaliacoes
              WHERE (? IS NULL OR nota >= ?) AND (? IS NULL OR nota <= ?)
                AND (? IS NULL OR situacao_entrega = ?)
              QUALIFY row_number() OVER (
                  PARTITION BY lower(texto) ORDER BY score DESC, review_id ASC
              ) = 1
              ORDER BY score DESC, review_id ASC LIMIT ?"""
    return con.execute(sql, [vetor.tolist(), nota_min, nota_min,
                             nota_max, nota_max, situacao_entrega, situacao_entrega, k]).df()


def carregar_corpus(caminho: Path) -> pd.DataFrame:
    """Preserva metadados de todas as avaliações; a busca agrupa após filtrar."""
    return pd.read_parquet(caminho).reset_index(drop=True)


def gerar_vetores(docs: pd.DataFrame, modelo: SentenceTransformer | None = None) -> np.ndarray:
    modelo = modelo or SentenceTransformer(MODELO)
    return np.asarray(modelo.encode(docs.texto.tolist(), batch_size=128,
                                    normalize_embeddings=True, show_progress_bar=True), dtype=np.float32)


def codificar_pergunta(modelo: SentenceTransformer, pergunta: str) -> np.ndarray:
    """Usa o mesmo modelo dos documentos e normaliza para busca por cosseno."""
    return np.asarray(modelo.encode(pergunta, normalize_embeddings=True), dtype=np.float32)
