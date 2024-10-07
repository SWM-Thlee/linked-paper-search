from typing import List

from fastapi import APIRouter, Request
from haystack import Document
from models.document import DocumentMeta, DocumentResponse

router = APIRouter()


@router.get("/")
async def read_root():
    return {"message": "Healthy"}


@router.get("/search", response_model=List[DocumentResponse])
async def search(request: Request, query: str):
    results: List[DocumentResponse] = await request.app.state.search_service.query(
        query
    )

    return results


@router.get("/correlations", response_model=List[DocumentResponse])
async def get_cores(request: Request, doc_id: str):
    results: List[DocumentResponse] = (
        await request.app.state.search_service.similar_docs(doc_id)
    )

    return results
