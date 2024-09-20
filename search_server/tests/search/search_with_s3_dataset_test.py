import unittest

from repositories.vector_db import MemoryVectorDB
from services.embedding import SentenceEmbeddingService
from services.search import SearchService
from utils.dataset import download_dataset, parse_xml_to_dict

s3_bucket = "paper-feed"
test_dataset_keys = ["01-arxiv-raw/cs/arXivRaw_2024-Q2_043.xml"]

top_k = 10


class MyTestCase(unittest.TestCase):
    def setUp(self):
        embedding_service = SentenceEmbeddingService()
        db = MemoryVectorDB()

        # Get test dataset from S3, Insert to Memory DB
        for dataset_key in test_dataset_keys:
            dataset = download_dataset(s3_bucket, dataset_key)
            papers = parse_xml_to_dict(dataset).get("records")
            for paper in papers:
                metadata = paper.get("metadata")
                db.insert_item(
                    embedding_service.embed_text(metadata.get("title")), paper
                )

        self.search_service = SearchService(db, embedding_service)

    def test_search_service(self):
        results = self.search_service.search_similar("hello world", top_k=top_k)
        assert len(results) == top_k


if __name__ == "__main__":
    unittest.main()
