"""
Download MentalChat16K, clean, chunk, embed, and load into ChromaDB.
Run: python scripts/ingest_mentalchat16k.py [--limit N] [--model minilm|bge|simple|hf-api]
"""
import argparse
import hashlib
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

import chromadb
from app.utils.embeddings import (
    embed_texts,
    model_name_for,
    resolve_embedding_backend,
)


def load_dataset(limit: int | None):
    from datasets import load_dataset

    token = os.getenv("HF_TOKEN")
    ds = load_dataset("ShenLab/MentalChat16K", token=token)
    split = ds["train"] if "train" in ds else list(ds.values())[0]
    if limit:
        split = split.select(range(min(limit, len(split))))
    return split


def row_to_text(row) -> str:
    parts = []
    for key in ("instruction", "input", "output", "question", "answer", "text", "conversation"):
        if key in row and row[key]:
            val = row[key]
            if isinstance(val, list):
                val = "\n".join(str(v) for v in val)
            parts.append(str(val))
    if not parts:
        parts.append(str(row))
    return "\n".join(parts).strip()


def clean_rows(rows: list[str]) -> list[str]:
    seen = set()
    cleaned = []
    for text in rows:
        text = " ".join(text.split())
        if len(text) < 50:
            continue
        h = hashlib.md5(text.encode()).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        cleaned.append(text)
    return cleaned


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        tokens = enc.encode(text)
        chunks = []
        start = 0
        while start < len(tokens):
            end = start + chunk_size
            chunk_tokens = tokens[start:end]
            chunks.append(enc.decode(chunk_tokens))
            start += chunk_size - overlap
        return chunks
    except Exception:
        words = text.split()
        chunks = []
        size = chunk_size
        ov = overlap
        start = 0
        while start < len(words):
            end = start + size
            chunks.append(" ".join(words[start:end]))
            start += size - ov
        return chunks


def upsert_batches(collection, chunks: list[str], backend, model_name: str, batch_size: int = 32):
    hf_token = os.getenv("HF_TOKEN", "")
    effective_backend = backend
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i : i + batch_size]
        ids = [f"chunk_{i + j}" for j in range(len(batch))]
        embeddings, used_backend = embed_texts(
            batch,
            effective_backend,
            model_name,
            hf_token=hf_token or None,
        )
        if used_backend != effective_backend:
            effective_backend = used_backend
            collection.modify(metadata={"embedding_backend": effective_backend})
            print(f"Switched collection embedding backend to {effective_backend}.")
        collection.upsert(documents=batch, ids=ids, embeddings=embeddings)
        print(f"Upserted {i + len(batch)}/{len(chunks)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=500, help="Max rows to process (demo)")
    parser.add_argument(
        "--model",
        choices=["minilm", "bge", "st", "st-bge", "hf-api", "simple"],
        default="minilm",
        help="minilm/bge auto-fallback if local ML unavailable; simple=offline hash; hf-api=HuggingFace",
    )
    parser.add_argument("--chroma-host", default=os.getenv("CHROMA_HOST", "localhost"))
    parser.add_argument("--chroma-port", type=int, default=int(os.getenv("CHROMA_PORT", "8000")))
    args = parser.parse_args()

    print(f"Loading dataset (limit={args.limit})...")
    split = load_dataset(args.limit)
    texts = [row_to_text(row) for row in split]
    texts = clean_rows(texts)
    print(f"Cleaned {len(texts)} conversations")

    all_chunks = []
    for t in texts:
        all_chunks.extend(chunk_text(t))
    print(f"Generated {len(all_chunks)} chunks")

    client = chromadb.HttpClient(host=args.chroma_host, port=args.chroma_port)
    collection_name = os.getenv("CHROMA_COLLECTION", "mental_health_knowledge")
    try:
        client.delete_collection(collection_name)
        print(f"Reset existing collection: {collection_name}")
    except Exception:
        pass

    if args.model in ("simple", "hf-api"):
        backend = args.model  # type: ignore[assignment]
        model_name = model_name_for("minilm")
        if backend == "hf-api" and not os.getenv("HF_TOKEN"):
            raise ValueError("HF_TOKEN required for --model hf-api")
    else:
        backend, model_name = resolve_embedding_backend(args.model, os.getenv("HF_TOKEN"))

    print(f"Embedding backend: {backend} ({model_name})")
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"embedding_backend": backend, "embedding_model": model_name},
    )
    upsert_batches(collection, all_chunks, backend, model_name)
    print(f"Ingestion complete. Collection '{collection_name}' has {collection.count()} documents.")


if __name__ == "__main__":
    main()
