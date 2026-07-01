"""Локальные эмбеддинги без внешнего API."""

import hashlib
import math
import re

from app.config import get_settings

_DIM = 384
_model = None


def _hash_embed(text: str) -> list[float]:
    vec = [0.0] * _DIM
    tokens = re.findall(r"[а-яёa-z0-9]+", text.lower())
    for token in tokens:
        h = int(hashlib.md5(token.encode("utf-8")).hexdigest(), 16)
        for i in range(8):
            idx = (h >> (i * 8)) % _DIM
            vec[idx] += 1.0
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def _get_fastembed_model():
    global _model
    if _model is None:
        from fastembed import TextEmbedding

        _model = TextEmbedding(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    return _model


def embed_text(text: str) -> list[float]:
    settings = get_settings()
    if settings.use_local_embeddings:
        try:
            model = _get_fastembed_model()
            return list(model.embed([text[:8000]]))[0].tolist()
        except Exception:
            return _hash_embed(text)
    return _hash_embed(text)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)
