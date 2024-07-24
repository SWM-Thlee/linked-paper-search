from contextlib import asynccontextmanager

from fastapi import FastAPI
from repositories.vector_db import MemoryVectorDB
from routes.api_endpoints import router as main_router
from services.embedding import SentenceEmbeddingService
from services.search import SearchService


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.embedding_service = SentenceEmbeddingService()
    app.state.db = MemoryVectorDB()
    app.state.search_service = SearchService(app.state.db, app.state.embedding_service)
    try:
        yield
    finally:
        # clear db
        app.state.db.clear()


app = FastAPI(lifespan=lifespan)
app.include_router(main_router)
