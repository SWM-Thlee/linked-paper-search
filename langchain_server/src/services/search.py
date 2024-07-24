from enum import Enum, auto

from repositories.vector_db import VectorDB
from services.embedding import EmbeddingService
from utils.logger import log_on_init


class SearchMethod(Enum):
    COSINE = auto()
    EUCLIDEAN = auto()


@log_on_init("uvicorn.info")
class SearchService:
    def __init__(self, db: VectorDB, embedding_service: EmbeddingService):
        self.db = db
        self.embedding_service = embedding_service

    def search_similar(
        self, query: str, method: SearchMethod = SearchMethod.COSINE, top_k: int = 10
    ):
        vector = self.embedding_service.embed_text(query)
        # 유사도 검색 메서드 선택
        if method == SearchMethod.COSINE:
            return self.db.find_with_cosine_similarity(vector, top_k)
        elif method == SearchMethod.EUCLIDEAN:
            return self.db.find_with_euclidean_similarity(vector, top_k)
