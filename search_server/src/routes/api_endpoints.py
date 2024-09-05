from typing import List

from fastapi import APIRouter, Request
from haystack import Document
from models.document import DocumentResponse

router = APIRouter()


@router.get("/search", response_model=List[DocumentResponse])
async def search(request: Request, query: str):
    results: List[Document] = request.app.state.search_service.query(query)
    documents = []
    for doc in results:
        document = DocumentResponse(content=doc.content, meta=doc.meta)
        documents.append(document)
    return documents
