from contextlib import asynccontextmanager

from fastapi import FastAPI
from repositories.vector_db import MemoryVectorDB
from services.embedding import BertEmbeddingService, SentenceEmbeddingService
from services.search import SearchMethod, SearchService

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
        yield
    finally:
        # close db connection
        app.state.db.clear()
