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

    def _truncate_query(self, query: str, max_length: int = 60) -> str:
        if len(query) <= max_length:
            return query
        # 최대 길이 내에서 띄어쓰기 기준으로 자르기
        truncated_query = query[:max_length].rsplit(" ", 1)[0]
        return truncated_query

    async def query(
        self,
        query_sentence: str,
        **kwargs,
    ) -> List[DocumentResponse]:
        filter_categoreis = kwargs.get("filter_categories")
        filter_start_date = kwargs.get("filter_start_date")
        filter_end_date = kwargs.get("filter_end_date")

        filters = get_filters(filter_categoreis, filter_start_date, filter_end_date)

        # query_sentence = self._truncate_query(query_sentence)

        # loop = asyncio.get_event_loop()
        result = self.hybrid_retrieval.run(
            {
                "text_embedder": {
                    "text": query_sentence,
                },
                "embedding_retriever": {
                    "filters": filters,
                },
                "bm25_retriever": {
                    "query": query_sentence,
                    "filters": filters,
                },
                "ranker": {"query": query_sentence},
            }
        )

        results: List[Document] = result["ranker"]["documents"]
        documents = []
        for doc in results:
            document = DocumentResponse(id=doc.id, meta=doc.meta, weight=doc.score)
            documents.append(document)
        return documents
