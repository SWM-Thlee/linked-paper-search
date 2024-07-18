import unittest

from repositories.vector_db import MemoryVectorDB
from services.embedding import SentenceEmbeddingService
from services.search import SearchMethod, SearchService


class MyTestCase(unittest.TestCase):
    def setUp(self):
        # MemoryVectorDB 인스턴스를 생성하고 몇 개의 벡터를 추가합니다.
        embedding_service = SentenceEmbeddingService()

        db = MemoryVectorDB()
        db.clear()  # 이전 데이터 초기화

        dataset = {
            1: "Securing Confidential Data For Distributed Software Development Teams: Encrypted Container File",
            2: "Distributed Inference Performance Optimization for LLMs on CPUs",
            3: "Sensible and Sensitive AI for Worker Wellbeing: Factors that Inform Adoption and Resistance for "
            "Information Workers",
            4: "Khronos: A Unified Approach for Spatio-Temporal Metric-Semantic SLAM in Dynamic Environments",
            5: "A Design Space for Intelligent and Interactive Writing Assistants",
        }
        db.insert_item(embedding_service.embed_text(dataset[1]), 1)
        db.insert_item(embedding_service.embed_text(dataset[2]), 2)
        db.insert_item(embedding_service.embed_text(dataset[3]), 3)
        db.insert_item(embedding_service.embed_text(dataset[4]), 4)
        db.insert_item(embedding_service.embed_text(dataset[5]), 5)

        self.search_service = SearchService(db, embedding_service)

    def test_cosine_similarity_search(self):
        # 코사인 유사도로 가장 유사한 벡터 찾기
        query_text = "Securing Confidential"

        result = self.search_service.search_similar(query_text, SearchMethod.COSINE)
        # 예상 결과가 'cat'이라고 가정
        print(result)
        self.assertEqual(result[0]["metadata"], 1)

    def test_euclidean_similarity_search(self):
        # 유클리드 거리로 가장 가까운 벡터 찾기
        query_text = "Securing Confidential"

        result = self.search_service.search_similar(query_text, SearchMethod.EUCLIDEAN)
        # 예상 결과가 'cat'이라고 가정
        print(result)
        self.assertEqual(result[0]["metadata"], 1)


if __name__ == "__main__":
    unittest.main()
