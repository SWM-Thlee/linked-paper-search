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
from services.ranker import RankerService
from utils.filter import get_filters
from utils.logger import log_on_init


@log_on_init()
class CorrelationService:
    def __init__(
        self,
        document_store: OpenSearchDocumentStore,
        ranker: RankerService,
        top_k=10,
        vector_store: InMemoryVectorStore = None,
    ):
        self.bm25_retriever = OpenSearchBM25Retriever(
            document_store=document_store,
            top_k=top_k,
        )

        # bm25_retriever = OpenSearchBM25Retriever(
        #     document_store=document_store,
        #     top_k=top_k,
        # )

        embedding_retriever = OpenSearchEmbeddingRetriever(
            document_store=document_store,
        )
        # document_joiner = DocumentJoiner()

        self.correlation_pipleline = Pipeline()
        self.correlation_pipleline.add_component(
            "embedding_retriever", embedding_retriever
        )
        # self.correlation_pipleline.add_component("bm25_retriever", bm25_retriever)
        # self.correlation_pipleline.add_component("document_joiner", document_joiner)
        self.correlation_pipleline.add_component("ranker", ranker)

        # self.correlation_pipleline.connect("bm25_retriever", "document_joiner")
        # self.correlation_pipleline.connect("embedding_retriever", "document_joiner")
        # self.correlation_pipleline.connect("document_joiner", "ranker")
        self.correlation_pipleline.connect("embedding_retriever", "ranker")

        self.correlation_pipleline.warm_up()  # lazy loading 방지 (model download, db connection ...)

        self._vector_store = (
            vector_store  # openSearch로 가져온 document를 캐시할 vector store
        )

    async def similar_docs(
        self, doc_id: str, top_k: int = 10, **kwargs
    ) -> List[DocumentResponse]:
        source_doc = None
        try:
            source_doc = self._vector_store.get_entity(doc_id)

        except ValueError as e:
            # vector store에 없는 경우 document store에서 가져와서 저장
            query_result = self.bm25_retriever.run(
                query=doc_id,
                top_k=1,
                filters={
                    "operator": "AND",
                    "conditions": [
                        {"field": "id", "operator": "==", "value": doc_id},
                    ],
                },
            )
            results: List[Document] = query_result["documents"]
            source_doc = TempDocument(
                results[0].id, results[0].embedding, results[0].content
            )

        if source_doc:
            doc_vector = source_doc.embedding
            filter_categoreis = kwargs.get("filter_categories")
            filter_start_date = kwargs.get("filter_start_date")
            filter_end_date = kwargs.get("filter_end_date")
            filters = get_filters(filter_categoreis, filter_start_date, filter_end_date)
            query_result = self.correlation_pipleline.run(
                {
                    "embedding_retriever": {
                        "query_embedding": doc_vector,
                        "filters": filters,
                        "top_k": top_k * 2,
                    },
                    "ranker": {
                        "query": source_doc.content,
                        "top_k": top_k,
                    },
                }
            )
            similar_docs: List[Document] = query_result["ranker"]["documents"]
            documents = []
            for doc in similar_docs:
                entity = TempDocument(doc.id, doc.embedding, doc.content)
                self._vector_store.set(doc.id, entity)
                if source_doc.id == doc.id:
                    doc.score = 1.0  # 자기 자신은 1.0으로 설정
                document = DocumentResponse(id=doc.id, meta=doc.meta, weight=doc.score)
                documents.append(document)
            return documents
