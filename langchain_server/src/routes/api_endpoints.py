from config import SEARCH_METHOD
from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/embedding")
async def get_embedding(request: Request, query: str):
    vector = request.app.state.embedding_service.embed_text(query)
    return {"embedding": vector}


@router.get("/search")
async def search(request: Request, query: str):
    similar_items = request.app.state.search_service.search_similar(
        query, SEARCH_METHOD
    )
    return {"results": similar_items}
