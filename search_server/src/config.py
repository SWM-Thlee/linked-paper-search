import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from repositories.document_store import AwsOpenSearch, LocalOpenSearch
from services.embedding import BgeM3SetenceEmbedder
from services.ranker import RankerService
from services.search import SearchService
from utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    fast api life cycle동안 singleton으로 사용할 search service 생성
    """
    environment = os.getenv("ENVIRONMENT", "dev")
    logger.info(f"environment: {environment}")

    if environment == "prod":
        # prod 환경에 맞춘 Document Store
        document_store = AwsOpenSearch()
    else:
        # dev 환경에 맞춘 Document Store
        document_store = LocalOpenSearch()

    text_embedder = BgeM3SetenceEmbedder()
    ranker = RankerService()
    app.state.search_service = SearchService(
        text_embedder=text_embedder,
        document_store=document_store,
        ranker=ranker,
    )

    yield
