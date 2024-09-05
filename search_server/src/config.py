from contextlib import asynccontextmanager

from fastapi import FastAPI
from repositories.document_store import AwsOpenSearch, LocalOpenSearch
from services.embedding import BgeM3SetenceEmbedder
from services.ranker import RankerService
from services.search import SearchService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    fast api life cycle동안 singleton으로 사용할 search service 생성
    """
    text_embedder = BgeM3SetenceEmbedder()
    document_store = LocalOpenSearch()
    ranker = RankerService()
    app.state.search_service = SearchService(
        text_embedder=text_embedder,
        document_store=document_store,
        ranker=ranker,
    )

    yield
