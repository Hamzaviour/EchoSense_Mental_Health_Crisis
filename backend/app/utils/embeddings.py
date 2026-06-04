"""Embedding helpers with fallbacks for environments without working torch/onnxruntime."""

from __future__ import annotations

import hashlib
import os
from typing import Literal

import requests

Backend = Literal["sentence-transformers", "onnx", "hf-api", "simple"]

SIMPLE_EMBED_DIM = 384
HF_EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

MODEL_ALIASES: dict[str, str] = {
    "minilm": HF_EMBED_MODEL,
    "bge": "BAAI/bge-large-en-v1.5",
    "st": HF_EMBED_MODEL,
    "st-bge": "BAAI/bge-large-en-v1.5",
}


def model_name_for(alias: str) -> str:
    return MODEL_ALIASES.get(alias, alias)


def embed_simple(texts: list[str], dim: int = SIMPLE_EMBED_DIM) -> list[list[float]]:
    vectors = []
    for text in texts:
        vec = [0.0] * dim
        for word in text.lower().split():
            digest = hashlib.sha256(word.encode()).digest()
            for i in range(dim):
                byte = digest[i % len(digest)]
                vec[i] += (byte / 127.5) - 1.0
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        vectors.append([v / norm for v in vec])
    return vectors


def _can_import_onnx() -> bool:
    try:
        import onnxruntime  # noqa: F401

        return True
    except Exception:
        return False


def _can_import_sentence_transformers() -> bool:
    try:
        import torch  # noqa: F401
        from sentence_transformers import SentenceTransformer  # noqa: F401

        return True
    except Exception:
        return False


def resolve_embedding_backend(model_alias: str, hf_token: str | None = None) -> tuple[Backend, str]:
    """Pick the best available backend for the requested model alias."""
    model_name = model_name_for(model_alias)

    if _can_import_sentence_transformers():
        return "sentence-transformers", model_name

    if _can_import_onnx():
        return "onnx", model_name

    token = hf_token or os.getenv("HF_TOKEN", "")
    if token:
        print(
            "Local embedding libraries unavailable (torch/onnxruntime). "
            "Falling back to Hugging Face Inference API."
        )
        return "hf-api", HF_EMBED_MODEL

    print(
        "WARNING: Local embeddings unavailable and HF_TOKEN not set. "
        "Using offline hash embeddings (lower retrieval quality). "
        "Set HF_TOKEN in .env for better results, or use Python 3.11/3.12 with torch."
    )
    return "simple", HF_EMBED_MODEL


def embed_via_hf_api(
    texts: list[str],
    token: str,
    model: str = HF_EMBED_MODEL,
    batch_size: int = 8,
) -> list[list[float]]:
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {token}"}
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        for attempt in range(3):
            resp = requests.post(url, headers=headers, json={"inputs": batch}, timeout=120)
            if resp.status_code == 503:
                import time

                time.sleep(10)
                continue
            resp.raise_for_status()
            data = resp.json()
            break
        else:
            raise RuntimeError("HF Inference API unavailable after retries")

        for item in data:
            if isinstance(item[0], list):
                dim = len(item[0])
                pooled = [sum(row[d] for row in item) / len(item) for d in range(dim)]
            else:
                pooled = item
            all_embeddings.append(pooled)

        print(f"Embedded {min(i + batch_size, len(texts))}/{len(texts)} via HF API")

    return all_embeddings


def embed_with_sentence_transformers(texts: list[str], model_name: str) -> list[list[float]]:
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(model_name)
    vectors = model.encode(texts, normalize_embeddings=True)
    return vectors.tolist()


def embed_with_onnx(texts: list[str]) -> list[list[float]]:
    from chromadb.utils.embedding_functions import DefaultEmbeddingFunction

    return DefaultEmbeddingFunction()(texts)


def embed_texts(
    texts: list[str],
    backend: Backend,
    model_name: str,
    hf_token: str | None = None,
    *,
    allow_simple_fallback: bool = True,
) -> tuple[list[list[float]], Backend]:
    try:
        if backend == "sentence-transformers":
            return embed_with_sentence_transformers(texts, model_name), backend
        if backend == "onnx":
            return embed_with_onnx(texts), backend
        if backend == "hf-api":
            token = hf_token or os.getenv("HF_TOKEN", "")
            if not token:
                raise ValueError("HF_TOKEN required for hf-api embeddings")
            return embed_via_hf_api(texts, token, model=model_name), backend
        return embed_simple(texts), "simple"
    except Exception as exc:
        if not allow_simple_fallback or backend == "simple":
            raise
        print(
            f"WARNING: {backend} embedding failed ({exc}). "
            "Falling back to offline hash embeddings."
        )
        return embed_simple(texts), "simple"


def embed_query(query: str, backend: Backend, model_name: str, hf_token: str | None = None) -> list[float]:
    vectors, _ = embed_texts([query], backend, model_name, hf_token=hf_token, allow_simple_fallback=True)
    return vectors[0]
