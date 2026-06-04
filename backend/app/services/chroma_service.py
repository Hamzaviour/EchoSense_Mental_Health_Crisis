from flask import current_app

_embedding_fn = None


def _collection_embedding_meta(col) -> tuple[str, str]:
    meta = getattr(col, "metadata", None) or {}
    backend = meta.get("embedding_backend", "")
    model = meta.get("embedding_model") or current_app.config.get(
        "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
    )
    if not backend:
        from app.utils.embeddings import resolve_embedding_backend

        backend, model = resolve_embedding_backend("minilm", current_app.config.get("HF_TOKEN"))
    return backend, model


def _embedding_function():
    global _embedding_fn
    if _embedding_fn is None:
        from chromadb.utils import embedding_functions

        model = current_app.config.get(
            "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        )
        try:
            _embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=model
            )
        except Exception:
            try:
                _embedding_fn = embedding_functions.DefaultEmbeddingFunction()
            except Exception:
                _embedding_fn = None
    return _embedding_fn


def get_chroma_client():
    import chromadb

    host = current_app.config.get("CHROMA_HOST", "localhost")
    port = current_app.config.get("CHROMA_PORT", 8000)
    return chromadb.HttpClient(host=host, port=port)


def get_knowledge_collection():
    client = get_chroma_client()
    name = current_app.config.get("CHROMA_COLLECTION", "mental_health_knowledge")
    try:
        return client.get_collection(name=name)
    except Exception:
        return client.get_or_create_collection(
            name=name, embedding_function=_embedding_function()
        )


def get_patient_memory_collection():
    client = get_chroma_client()
    name = current_app.config.get(
        "CHROMA_PATIENT_MEMORY_COLLECTION", "patient_session_memory"
    )
    return client.get_or_create_collection(name=name, embedding_function=_embedding_function())


def _embed_query(query: str, backend: str, model_name: str) -> list[float]:
    from app.utils.embeddings import embed_query

    token = current_app.config.get("HF_TOKEN", "")
    return embed_query(query, backend, model_name, hf_token=token or None)


def retrieve_context(query: str, k: int = 5) -> tuple[list[str], list[str]]:
    try:
        col = get_knowledge_collection()
        backend, model_name = _collection_embedding_meta(col)
        try:
            if backend in ("simple", "hf-api", "sentence-transformers", "onnx"):
                q_emb = _embed_query(query, backend, model_name)
                results = col.query(query_embeddings=[q_emb], n_results=k)
            else:
                results = col.query(query_texts=[query], n_results=k)
        except Exception:
            q_emb = _embed_query(query, backend if backend else "simple", model_name)
            results = col.query(query_embeddings=[q_emb], n_results=k)
        docs = results.get("documents", [[]])[0] or []
        ids = results.get("ids", [[]])[0] or []
        return docs, ids
    except Exception:
        return [], []


def store_patient_memory(patient_id: str, summary: str, session_id: int):
    try:
        col = get_patient_memory_collection()
        doc_id = f"{patient_id}_{session_id}"
        col.upsert(
            documents=[summary],
            ids=[doc_id],
            metadatas=[{"patient_id": patient_id, "session_id": session_id}],
        )
    except Exception:
        pass


def retrieve_patient_memory(patient_id: str, query: str, k: int = 3) -> list[str]:
    try:
        col = get_patient_memory_collection()
        results = col.query(
            query_texts=[query],
            n_results=k,
            where={"patient_id": patient_id},
        )
        return results.get("documents", [[]])[0] or []
    except Exception:
        return []
