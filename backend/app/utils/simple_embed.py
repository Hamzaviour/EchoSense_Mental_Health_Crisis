from app.utils.embeddings import SIMPLE_EMBED_DIM, embed_simple


def embed_text(text: str, dim: int = SIMPLE_EMBED_DIM) -> list[float]:
    return embed_simple([text], dim=dim)[0]
