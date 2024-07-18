from contextlib import asynccontextmanager

from fastapi import FastAPI
from repositories.vector_db import MemoryVectorDB
from services.embedding import BertEmbeddingService, SentenceEmbeddingService
from services.search import SearchMethod, SearchService
from utils.dataset import download_dataset_from_s3, parse_xml_to_dict

s3_bucket = "paper-feed"
test_dataset_keys = [
    "01-arxiv-raw/cs/arXivRaw_2024-Q2_043.xml",
    "01-arxiv-raw/cs/arXivRaw_2024-Q2_044.xml",
    "01-arxiv-raw/cs/arXivRaw_2024-Q2_045.xml",
    "01-arxiv-raw/cs/arXivRaw_2024-Q2_046.xml",
]

SEARCH_METHOD = SearchMethod.EUCLIDEAN


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    fast api life cycle동안 singleton으로 사용할 search service, db connection instance 삽입
    :param app:
    :return:
    """

    app.state.embedding_service = SentenceEmbeddingService()
    app.state.db = MemoryVectorDB()
    app.state.search_service = SearchService(app.state.db, app.state.embedding_service)
    try:
        # db connection pool setup or insert test dataset
        for test_dataset_key in test_dataset_keys:
            test_dataset_xml = download_dataset_from_s3(s3_bucket, test_dataset_key)
            dataset = parse_xml_to_dict(test_dataset_xml)
            for record in dataset["records"]:
                metadata = record["metadata"]

                title = metadata["title"]
                abstract = metadata["abstract"]
                app.state.db.insert_item(
                    app.state.embedding_service.embed_text(title),
                    metadata,
                )

        yield
    finally:
        # close db connection
        app.state.db.clear()
