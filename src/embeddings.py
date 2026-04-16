import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class TFIDFIndex:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.matrix = None
        self.chunks = []

    def build(self, chunks: list[dict]) -> None:
        self.chunks = chunks
        texts = [c["content"] for c in chunks]
        self.matrix = self.vectorizer.fit_transform(texts)

    def query(self, question: str, top_k: int = 3) -> list[dict]:
        if self.matrix is None or not self.chunks:
            return []

        q_vec = self.vectorizer.transform([question])
        scores = cosine_similarity(q_vec, self.matrix).flatten()
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0:
                results.append({
                    **self.chunks[idx],
                    "score": float(scores[idx]),
                })
        return results
