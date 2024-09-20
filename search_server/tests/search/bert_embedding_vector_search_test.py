import unittest

from repositories.vector_db import MemoryVectorDB
from services.embedding import BertEmbeddingService
from services.search import SearchMethod, SearchService


class MyTestCase(unittest.TestCase):
    def setUp(self):
        # MemoryVectorDB 인스턴스를 생성하고 몇 개의 벡터를 추가합니다.
        embedding_service = BertEmbeddingService()

        db = MemoryVectorDB()
        db.clear()  # 이전 데이터 초기화
        db.insert_item(embedding_service.embed_text("cat"), "cat")
        db.insert_item(embedding_service.embed_text("dog"), "dog")
        db.insert_item(embedding_service.embed_text("human"), "human")
        db.insert_item(embedding_service.embed_text("banana"), "banana")

        self.search_service = SearchService(db, embedding_service)

    def test_cosine_similarity_search(self):
        # 코사인 유사도로 가장 유사한 벡터 찾기
        query_text = "kitty"

        result = self.search_service.search_similar(query_text, SearchMethod.COSINE)
        # 예상 결과가 'cat'이라고 가정
        self.assertEqual(result[0]["metadata"], "cat")

    def test_euclidean_similarity_search(self):
        # 유클리드 거리로 가장 가까운 벡터 찾기
        query_text = "kitty"

        result = self.search_service.search_similar(query_text, SearchMethod.EUCLIDEAN)
        # 예상 결과가 'cat'이라고 가정
        self.assertEqual(result[0]["metadata"], "cat")


if __name__ == "__main__":
    unittest.main()
