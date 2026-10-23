"""Contrato de resposta: citação válida é necessária, mas não prova suporte semântico."""
from dataclasses import dataclass, field
from typing import Callable

import duckdb

from src.retrieval.indice import buscar, codificar_pergunta


@dataclass(frozen=True)
class Resposta:
    status: str
    texto: str
    review_ids: list[str] = field(default_factory=list)


def _recusar(motivo: str) -> Resposta:
    return Resposta("sem_evidencia", motivo)


def _erro(motivo: str) -> Resposta:
    return Resposta("erro_geracao", motivo)


def responder(pergunta: str, evidencias: list[dict],
             gerar: Callable[[str, list[dict]], dict]) -> Resposta:
    """Valida a estrutura da resposta; suficiência factual requer avaliação separada."""
    if not isinstance(pergunta, str) or not pergunta.strip():
        return _recusar("Pergunta vazia ou inválida.")
    if not isinstance(evidencias, list) or not evidencias:
        return _recusar("Nenhuma avaliação recuperada.")
    if any(not isinstance(e, dict) or not isinstance(e.get("review_id"), str)
           or not e["review_id"] or not isinstance(e.get("texto"), str)
           for e in evidencias):
        return _erro("Contexto com avaliação inválida.")
    ids = {e["review_id"] for e in evidencias}
    if len(ids) != len(evidencias):
        return _erro("Contexto com identificadores ausentes ou duplicados.")
    try:
        saida = gerar(pergunta, evidencias)
    except Exception:
        return _erro("O serviço de geração falhou nesta consulta.")
    if (not isinstance(saida, dict) or not isinstance(saida.get("status"), str)
            or saida["status"] not in {"respondida", "sem_evidencia"}):
        return _erro("Saída inválida do modelo.")
    texto = saida.get("texto")
    citacoes = saida.get("review_ids")
    if not isinstance(texto, str) or not texto.strip() or not isinstance(citacoes, list):
        return _erro("Resposta sem texto ou citações válidas.")
    if any(not isinstance(i, str) or i not in ids for i in citacoes):
        return _erro("Resposta citou avaliações ausentes do contexto.")
    if saida["status"] == "sem_evidencia":
        return _recusar("As avaliações recuperadas não sustentam a resposta solicitada.")
    if not citacoes:
        return _erro("Resposta citou avaliações ausentes do contexto.")
    return Resposta("respondida", texto.strip(), list(dict.fromkeys(citacoes)))


def executar_rag(pergunta: str, con: duckdb.DuckDBPyConnection, modelo_embedding,
                gerar: Callable[[str, list[dict]], dict], k: int = 10,
                nota_min: int | None = None, nota_max: int | None = None,
                situacao_entrega: str | None = None, categoria: str | None = None,
                compra_de: str | None = None, compra_ate: str | None = None) -> Resposta:
    """Liga embedding, busca exata e geração; não responde frequência por top-k."""
    if not isinstance(pergunta, str) or not pergunta.strip():
        return _recusar("Pergunta vazia ou inválida.")
    try:
        vetor = codificar_pergunta(modelo_embedding, pergunta)
        achados = buscar(con, vetor, k=k, nota_min=nota_min,
                         nota_max=nota_max, situacao_entrega=situacao_entrega,
                         categoria=categoria, compra_de=compra_de, compra_ate=compra_ate)
    except Exception:
        return _erro("A recuperação de avaliações falhou nesta consulta.")
    evidencias = achados[["review_id", "texto"]].to_dict("records")
    return responder(pergunta, evidencias, gerar)
