from embeddings import TFIDFIndex
from config import TOP_K


def retrieve(query: str, index: TFIDFIndex, top_k: int = TOP_K) -> list[dict]:
    return index.query(query, top_k=top_k)
