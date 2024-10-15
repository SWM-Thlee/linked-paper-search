from abc import ABC, abstractmethod
from typing import OrderedDict

import numpy as np


class TempDocument:
    def __init__(self, id: str, embedding: np.ndarray, title: str):
        self.id = id
        self.embedding = embedding
        self.title = title


# 벡터 스토어의 기본 인터페이스 정의
class VectorStore(ABC):

    @abstractmethod
    def set(self, doc_id: str, entity: TempDocument) -> None:
        """벡터와 관련된 메타데이터를 스토어에 추가"""
        pass

    @abstractmethod
    def get_vector(self, doc_id: str) -> np.ndarray:
        """주어진 문서 ID에 해당하는 벡터 반환"""
        pass

    @abstractmethod
    def get_entity(self, doc_id: str) -> TempDocument:
        """주어진 문서 ID에 해당하는 엔티티 반환"""
        pass


class InMemoryVectorStore(VectorStore):
    def __init__(self, max_size: int = 1000):
        self.store = OrderedDict()  # 벡터를 value로 저장하는 OrderedDict (LRU 캐시)
        self.max_size = max_size

    def set(self, doc_id: str, entity: TempDocument):
        """벡터를 ID와 함께 스토어에 추가 또는 업데이트"""
        if doc_id in self.store:
            self.store.move_to_end(doc_id)
        self.store[doc_id] = entity

        if len(self.store) > self.max_size:
            self.store.popitem(last=False)  # 가장 오래된 항목 삭제

    def get_vector(self, doc_id: str):
        """주어진 문서 ID에 해당하는 벡터 반환"""
        entity: TempDocument = self.store.get(doc_id)
        if entity is not None:
            self.store.move_to_end(doc_id)
            return entity.embedding
        else:
            raise ValueError(f"Document ID {doc_id} not found in store")

    def get_entity(self, doc_id: str) -> TempDocument:
        """주어진 문서 ID에 해당하는 엔티티 반환"""
        entity: TempDocument = self.store.get(doc_id)
        if entity is not None:
            self.store.move_to_end(doc_id)
            return entity
        else:
            raise ValueError(f"Document ID {doc_id} not found in store")
