"""Embedding vectors using the all-MiniLM-L6-v2 sentence-transformers model."""

from sentence_transformers import SentenceTransformer

EMBEDDING_DIM = 384

_model = SentenceTransformer("all-MiniLM-L6-v2")


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    return _model.encode(texts).tolist()


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]
