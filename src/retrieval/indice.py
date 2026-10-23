"""Busca exata com vetores normalizados e filtros de metadados em DuckDB."""
from pathlib import Path
from datetime import date
import re

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
    # Fixtures antigos sem data continuam úteis para testar a busca sem recorte temporal.
    tabela["data_compra"] = (pd.to_datetime(docs["data_compra"], errors="raise")
                             if "data_compra" in docs else pd.NaT)
    tabela["vetor"] = list(vetores.astype(np.float32))
    con.register("entrada_indice", tabela)
    try:
        con.execute(f"CREATE OR REPLACE TABLE avaliacoes AS SELECT review_id, texto, nota, "
                    f"situacao_entrega, categorias, data_compra, "
                    f"vetor::FLOAT[{DIM}] AS vetor FROM entrada_indice")
    finally:
        con.unregister("entrada_indice")


def buscar(con: duckdb.DuckDBPyConnection, vetor: np.ndarray, k: int = 10,
           nota_min: int | None = None, nota_max: int | None = None,
           situacao_entrega: str | None = None, categoria: str | None = None,
           compra_de: str | None = None, compra_ate: str | None = None) -> pd.DataFrame:
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
    if categoria is not None and (not isinstance(categoria, str)
            or re.fullmatch(r"[a-z0-9_]+", categoria) is None):
        raise ValueError("categoria inválida")
    def data_valida(valor):
        if valor is None:
            return None
        if not isinstance(valor, str) or re.fullmatch(r"\d{4}-\d{2}-\d{2}", valor) is None:
            raise ValueError("data de compra deve usar AAAA-MM-DD")
        try:
            return date.fromisoformat(valor)
        except ValueError as erro:
            raise ValueError("data de compra inválida") from erro
    inicio, fim = data_valida(compra_de), data_valida(compra_ate)
    if inicio is not None and fim is not None and inicio > fim:
        raise ValueError("início do período posterior ao fim")
    if (inicio is not None or fim is not None) and not con.execute(
            "SELECT EXISTS(SELECT 1 FROM avaliacoes WHERE data_compra IS NOT NULL)").fetchone()[0]:
        raise ValueError("índice sem data_compra válida para filtro temporal")
    sql = f"""SELECT review_id, texto, nota, situacao_entrega,
                     array_cosine_similarity(vetor, ?::FLOAT[{DIM}]) AS score
              FROM avaliacoes
              WHERE (? IS NULL OR nota >= ?) AND (? IS NULL OR nota <= ?)
                AND (? IS NULL OR situacao_entrega = ?)
                AND (? IS NULL OR list_contains(string_split(categorias, '|'), ?))
                AND (? IS NULL OR CAST(data_compra AS DATE) >= ?)
                AND (? IS NULL OR CAST(data_compra AS DATE) <= ?)
              QUALIFY row_number() OVER (
                  PARTITION BY lower(texto) ORDER BY score DESC, review_id ASC
              ) = 1
              ORDER BY score DESC, review_id ASC LIMIT ?"""
    return con.execute(sql, [vetor.tolist(), nota_min, nota_min,
                             nota_max, nota_max, situacao_entrega, situacao_entrega,
                             categoria, categoria, inicio, inicio, fim, fim, k]).df()


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
