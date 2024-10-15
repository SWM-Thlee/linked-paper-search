import asyncio
from typing import List

from haystack import Document, Pipeline
from haystack.components.joiners import DocumentJoiner
from haystack_integrations.components.retrievers.opensearch import (
    OpenSearchBM25Retriever,
    OpenSearchEmbeddingRetriever,
)
from models.document import DocumentResponse
from repositories.document_store import OpenSearchDocumentStore
from repositories.vector_store import InMemoryVectorStore, TempDocument
from services.embedding import EmbeddingService
from services.ranker import RankerService
from utils.filter import get_filters
from utils.logger import log_on_init


@log_on_init()
class SearchService:
    def __init__(
        self,
        document_store: OpenSearchDocumentStore,
        ranker: RankerService,
        text_embedder: EmbeddingService,
        top_k=10,
    ):
        embedding_retriever = OpenSearchEmbeddingRetriever(
            document_store=document_store,
            top_k=top_k,
        )
        bm25_retriever = OpenSearchBM25Retriever(
            document_store=document_store,
            top_k=top_k,
        )
        document_joiner = DocumentJoiner()

        self.hybrid_retrieval = Pipeline()
        self.hybrid_retrieval.add_component("text_embedder", text_embedder)
        self.hybrid_retrieval.add_component("embedding_retriever", embedding_retriever)
        self.hybrid_retrieval.add_component("bm25_retriever", bm25_retriever)
        self.hybrid_retrieval.add_component("document_joiner", document_joiner)
        self.hybrid_retrieval.add_component("ranker", ranker)

        self.hybrid_retrieval.connect("text_embedder", "embedding_retriever")
        self.hybrid_retrieval.connect("bm25_retriever", "document_joiner")
        self.hybrid_retrieval.connect("embedding_retriever", "document_joiner")
        self.hybrid_retrieval.connect("document_joiner", "ranker")

        self.hybrid_retrieval.warm_up()  # lazy loading 방지 (model download, db connection ...)

    async def query(
        self,
        query: str,
        **kwargs,  # TODO: 검색 필터링 옵션 추가
    ) -> List[DocumentResponse]:
        filter_categoreis = kwargs.get("filter_categories")
        filter_start_date = kwargs.get("filter_start_date")
        filter_end_date = kwargs.get("filter_end_date")

        filters = get_filters(filter_categoreis, filter_start_date, filter_end_date)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self.hybrid_retrieval.run,
            {
                "text_embedder": {
                    "text": query,
                },
                "embedding_retriever": {
                    "filters": filters,
                },
                "bm25_retriever": {
                    "query": query,
                    "filters": filters,
                },
                "ranker": {"query": query},
            },
        )
        results: List[Document] = result["ranker"]["documents"]
        documents = []
        for doc in results:
            document = DocumentResponse(id=doc.id, meta=doc.meta, weight=doc.score)
            documents.append(document)
        return documents
