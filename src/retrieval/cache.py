"""Cache de embeddings vinculado aos textos em ordem e à configuração do encoder (spec 0005, 0010)."""
import hashlib
import io
import json
import logging
import os
from importlib.metadata import version
from pathlib import Path

import numpy as np


def _valido(emb: np.ndarray, formato: tuple[int, int]) -> bool:
    return (emb.shape == formato and np.issubdtype(emb.dtype, np.floating)
            and bool(np.isfinite(emb).all())
            and bool(np.allclose(np.linalg.norm(emb, axis=1), 1, atol=1e-4)))


def _substituir(destino: Path, gravar) -> None:
    # Grava ao lado e troca no fim: interrupção não deixa arquivo pela metade.
    temporario = destino.with_name(destino.name + ".tmp")
    try:
        gravar(temporario)
        os.replace(temporario, destino)
    finally:
        temporario.unlink(missing_ok=True)


def vetores_com_cache(cache: Path, modelo, textos: list[str], *, nome_modelo: str,
                      dimensao: int, prefixo: str = "") -> np.ndarray:
    identidade = {
        "schema": 1,
        "modelo": nome_modelo,
        "prefixo": prefixo,
        "normalize_embeddings": True,
        "sentence_transformers": version("sentence-transformers"),
        "dimensao": int(dimensao),
        "textos_sha256": hashlib.sha256(
            json.dumps(textos, ensure_ascii=False).encode("utf-8")
        ).hexdigest(),
    }
    manifesto = cache.with_suffix(".json")
    formato = (len(textos), identidade["dimensao"])
    if cache.exists() or manifesto.exists():
        try:
            metadados = json.loads(manifesto.read_text(encoding="utf-8"))
            if not isinstance(metadados, dict) or metadados.get("identidade") != identidade:
                raise ValueError("identidade diferente ou manifesto inválido")
            if metadados.get("vetores_sha256") != hashlib.sha256(cache.read_bytes()).hexdigest():
                raise ValueError("vetores não correspondem ao manifesto")
            emb = np.load(cache, allow_pickle=False)
            if not _valido(emb, formato):
                raise ValueError("formato ou valores de embeddings inválidos")
            return emb
        except (OSError, ValueError, EOFError) as erro:
            logging.getLogger(__name__).warning("Cache %s invalidado: %s; regenerando", cache.name, erro)
    emb = np.asarray(modelo.encode([prefixo + t for t in textos], batch_size=128,
                                   normalize_embeddings=True, show_progress_bar=True), dtype=np.float32)
    if not _valido(emb, formato):
        raise ValueError("encoder retornou embeddings incompatíveis ou não normalizados")
    cache.parent.mkdir(parents=True, exist_ok=True)
    # Manifesto por último: vetores novos com manifesto antigo falham no digest e regeneram.
    _substituir(cache, lambda caminho: caminho.write_bytes(_npy(emb)))
    _substituir(manifesto, lambda caminho: caminho.write_text(json.dumps({
        "identidade": identidade,
        "vetores_sha256": hashlib.sha256(cache.read_bytes()).hexdigest(),
    }, ensure_ascii=False, indent=2), encoding="utf-8"))
    return emb


def _npy(emb: np.ndarray) -> bytes:
    # np.save acrescenta ".npy" a nomes sem a extensão; bytes evitam isso no temporário.
    buffer = io.BytesIO()
    np.save(buffer, emb, allow_pickle=False)
    return buffer.getvalue()
