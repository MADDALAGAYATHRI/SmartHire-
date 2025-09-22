import os
import numpy as np
import faiss

class FaissStore:
    def __init__(self, path:str="/data/faiss.index", dim:int=256):
        self.path = path
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)
        self.ids = []  # parallel list mapping
        if os.path.exists(path):
            try:
                self.index = faiss.read_index(path)
                # ids persisted separately?
                if os.path.exists(path + ".ids"):
                    with open(path + ".ids","r") as f:
                        self.ids = [line.strip() for line in f.readlines()]
            except Exception:
                pass

    def _save(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        faiss.write_index(self.index, self.path)
        with open(self.path + ".ids","w") as f:
            for _id in self.ids:
                f.write(str(_id)+"\n")

    def add(self, vectors: np.ndarray, ids: list):
        if vectors.dtype != np.float32:
            vectors = vectors.astype("float32")
        self.index.add(vectors)
        self.ids.extend(ids)
        self._save()

    def search(self, query_vec: np.ndarray, top_k:int=5):
        if query_vec.dtype != np.float32:
            query_vec = query_vec.astype("float32")
        D, I = self.index.search(query_vec, top_k)
        return D, [self.ids[i] if 0 <= i < len(self.ids) else None for i in I.flatten()]
