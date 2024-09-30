from abc import ABC, abstractmethod
from typing import OrderedDict

import numpy as np


# 벡터 스토어의 기본 인터페이스 정의
class VectorStore(ABC):

    @abstractmethod
    def set(self, doc_id: str, vector: np.ndarray):
        """벡터와 관련된 메타데이터를 스토어에 추가"""
        pass

    @abstractmethod
    def get(self, doc_id: str):
        """주어진 문서 ID에 해당하는 벡터 반환"""
        pass


class InMemoryVectorStore(VectorStore):
    def __init__(self, max_size: int = 1000):
        self.store = OrderedDict()  # 벡터를 value로 저장하는 OrderedDict (LRU 캐시)
        self.max_size = max_size

    def set(self, doc_id: str, vector: np.ndarray):
        """벡터를 ID와 함께 스토어에 추가 또는 업데이트"""
        if doc_id in self.store:
            self.store.move_to_end(doc_id)
        self.store[doc_id] = vector

        if len(self.store) > self.max_size:
            self.store.popitem(last=False)  # 가장 오래된 항목 삭제

    def get(self, doc_id: str):
        """주어진 문서 ID에 해당하는 벡터 반환"""
        vector = self.store.get(doc_id)
        if vector is not None:
            self.store.move_to_end(doc_id)
            return vector
        else:
            raise ValueError(f"Document ID {doc_id} not found in store")
