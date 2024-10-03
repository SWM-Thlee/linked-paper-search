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
from repositories.vector_store import InMemoryVectorStore
from services.embedding import EmbeddingService
from services.ranker import RankerService
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
        self.embedding_retriever = OpenSearchEmbeddingRetriever(
            document_store=document_store,
            top_k=top_k,
        )
        self.bm25_retriever = OpenSearchBM25Retriever(
            document_store=document_store,
            top_k=top_k,
        )
        document_joiner = DocumentJoiner()

        self.hybrid_retrieval = Pipeline()
        self.hybrid_retrieval.add_component("text_embedder", text_embedder)
        self.hybrid_retrieval.add_component(
            "embedding_retriever", self.embedding_retriever
        )
        self.hybrid_retrieval.add_component("bm25_retriever", self.bm25_retriever)
        self.hybrid_retrieval.add_component("document_joiner", document_joiner)
        self.hybrid_retrieval.add_component("ranker", ranker)

        self.hybrid_retrieval.connect("text_embedder", "embedding_retriever")
        self.hybrid_retrieval.connect("bm25_retriever", "document_joiner")
        self.hybrid_retrieval.connect("embedding_retriever", "document_joiner")
        self.hybrid_retrieval.connect("document_joiner", "ranker")

        self.hybrid_retrieval.warm_up()  # lazy loading 방지 (model download, db connection ...)

        self.vector_store = InMemoryVectorStore()

    async def query(
        self,
        query: str,
        **kwargs,  # TODO: 검색 필터링 옵션 추가
    ) -> List[DocumentResponse]:
        filter_categoreis = kwargs.get("filter_categories")
        filter_start_date = kwargs.get("filter_start_date")
        filter_end_date = kwargs.get("filter_end_date")

        # 기본 필터 설정
        filters = {"operator": "AND", "conditions": []}

        # 날짜 필터 추가
        if filter_start_date:
            # 시작 날짜만 있는 경우 greater than or equal
            date_condition = {
                "field": "meta.datestamp",
                "operator": ">=",
                "value": filter_start_date,
            }
            filters["conditions"].append(date_condition)
        if filter_end_date:
            # 끝 날짜만 있는 경우 less than or equal
            date_condition = {
                "field": "meta.datestamp",
                "operator": "<=",
                "value": filter_end_date,
            }
            filters["conditions"].append(date_condition)

        # 필드 필터 추가
        if filter_categoreis:
            field_condition = {
                "field": "meta.categories",
                "operator": "in",
                "value": filter_categoreis,
            }
            filters["conditions"].append(field_condition)

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
            self.vector_store.set(doc.id, doc.embedding)
            document = DocumentResponse(id=doc.id, meta=doc.meta, weight=doc.score)
            documents.append(document)
        return documents

    async def similar_docs(
        self, doc_id: str, top_k: int = 10
    ) -> List[DocumentResponse]:
        try:
            doc_vector = self.vector_store.get(doc_id)

        except ValueError as e:
            result = self.bm25_retriever.run(
                query=doc_id, top_k=1, filters={"id": doc_id}
            )
            results: List[Document] = result["documents"]
            doc_vector = results[0].embedding
            self.vector_store.set(doc_id, doc_vector)

        finally:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,  # 기본 스레드 풀 사용
                self.embedding_retriever.run,
                doc_vector,
                None,
                top_k,
            )
            results: List[Document] = result["documents"]
            documents = []
            for doc in results:
                document = DocumentResponse(id=doc.id, meta=doc.meta, weight=doc.score)
                documents.append(document)
            return documents
