from typing import Annotated, List, Union

from fastapi import APIRouter, Query, Request
from haystack import Document
from models.document import DocumentMeta, DocumentResponse

router = APIRouter()


@router.get("/")
async def read_root():
    return {"message": "Healthy"}


@router.get("/search", response_model=List[DocumentResponse])
async def search(
    request: Request,
    query: str,
    filter_categories: Annotated[Union[list[str], None], Query()] = None,
    filter_start_date: str = None,
    filter_end_date: str = None,
):
    results: List[DocumentResponse] = await request.app.state.search_service.query(
        query,
        filter_categories=filter_categories,
        filter_start_date=filter_start_date,
        filter_end_date=filter_end_date,
    )

    return results


@router.get("/correlations", response_model=List[DocumentResponse])
async def get_cores(request: Request, doc_id: str):
    results: List[DocumentResponse] = (
        await request.app.state.search_service.similar_docs(doc_id)
    )

    return results
