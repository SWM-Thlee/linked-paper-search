from abc import ABC, abstractmethod

import numpy as np
from utils.logger import log_on_init


class VectorDB(ABC):
    @abstractmethod
    def find_with_cosine_similarity(self, vector, top_k=100):
        pass

    @abstractmethod
    def find_with_euclidean_similarity(self, vector, top_k=100):
        pass

    @abstractmethod
    def insert_item(self, vector, metadata=None):
        pass

    @abstractmethod
    def clear(self):
        pass


@log_on_init("uvicorn.info")
class MemoryVectorDB(VectorDB):

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MemoryVectorDB, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "vector_entries"):
            self.vector_entries = []

    def insert_item(self, vector, metadata=None):

        item = {"vector": vector}
        if metadata:
            item.update({"metadata": metadata})
        self.vector_entries.append(item)

    def clear(self):
        self.vector_entries = []

    def find_with_cosine_similarity(self, vector, top_k=100):
        vector = np.array(vector)
        similarities = np.array(
            [
                np.dot(vector, np.array(entry["vector"]))
                / (np.linalg.norm(vector) * np.linalg.norm(entry["vector"]))
                for entry in self.vector_entries
            ]
        )
        top_indices = np.argsort(-similarities)[:top_k]
        return [
            {
                "rank": idx + 1,
                "metadata": self.vector_entries[index]["metadata"],
                "similarity": similarities[index],
            }
            for idx, index in enumerate(top_indices)
        ]

    def find_with_euclidean_similarity(self, vector, top_k=100):
        vector = np.array(vector)
        distances = np.array(
            [
                np.linalg.norm(vector - np.array(entry["vector"]))
                for entry in self.vector_entries
            ]
        )
        top_indices = np.argsort(distances)[:top_k]
        return [
            {
                "rank": idx + 1,
                "metadata": self.vector_entries[index]["metadata"],
                "distance": distances[index],
            }
            for idx, index in enumerate(top_indices)
        ]
