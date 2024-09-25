from typing import List

from fastapi import APIRouter, Request
from haystack import Document
from models.document import DocumentMeta, DocumentResponse

router = APIRouter()


@router.get("/")
async def read_root():
    return {"message": "Hello, world!"}


@router.get("/search", response_model=List[DocumentResponse])
async def search(request: Request, query: str):
    results: List[Document] = request.app.state.search_service.query(query)
    documents = []
    for doc in results:
        document = DocumentResponse(id=doc.id, meta=doc.meta, weight=doc.score)
        documents.append(document)
    return documents
