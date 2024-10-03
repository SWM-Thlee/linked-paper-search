import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from haystack.utils import ComponentDevice, Device
from repositories.document_store import AwsOpenSearch, LocalOpenSearch
from services.embedding import BgeM3SetenceEmbedder
from services.ranker import BgeReRankderService
from services.search import SearchService
from utils.logger import logger

result_top_k = 50  # ranking 이후 상위 몇개의 결과를 가져올지 결정
index = "new_index9"
timeout = 900
use_ssl = True
verify_certs = True
embedding_dim = 1024
DEFAULT_REGION = "ap-northeast-2"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    fast api life cycle동안 singleton으로 사용할 search service 생성
    """
    environment = os.getenv("ENVIRONMENT", "dev")
    logger.info(f"environment: {environment}")

    if environment == "prod":
        # prod 환경에 맞춘 Document Store
        document_store = AwsOpenSearch(
            index=index,
            timeout=timeout,
            use_ssl=use_ssl,
            verify_certs=verify_certs,
            embedding_dim=embedding_dim,
            DEFAULT_REGION=DEFAULT_REGION,
        )
        device = ComponentDevice.from_str("cuda:0")
    else:
        # dev 환경에 맞춘 Document Store
        document_store = LocalOpenSearch(
            index=index,
            embedding_dim=embedding_dim,
            use_ssl=use_ssl,
        )
        device = ComponentDevice.from_str("mps")  # for local testing

    text_embedder = BgeM3SetenceEmbedder(device=device)
    ranker = BgeReRankderService(top_k=result_top_k, device=device)
    app.state.search_service = SearchService(
        text_embedder=text_embedder,
        document_store=document_store,
        ranker=ranker,
        top_k=result_top_k,
    )

    yield
