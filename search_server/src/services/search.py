from haystack import Pipeline
from haystack.components.joiners import DocumentJoiner
from haystack_integrations.components.retrievers.opensearch import (
    OpenSearchBM25Retriever,
    OpenSearchEmbeddingRetriever,
)
from repositories.document_store import OpenSearchDocumentStore
from services.embedding import EmbeddingService
from services.ranker import RankerService
from utils.logger import log_on_init

top_k = 100  # 검색 결과 중 상위 몇 개를 가져올지 결정


@log_on_init()
class SearchService:
    def __init__(
        self,
        document_store: OpenSearchDocumentStore,
        ranker: RankerService,
        text_embedder: EmbeddingService,
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

    def query(
        self,
        query: str,
        **kwargs,  # TODO: 검색 필터링 옵션 추가
    ):
        result = self.hybrid_retrieval.run(
            {
                "text_embedder": {"text": query},
                "bm25_retriever": {"query": query},
                "ranker": {"query": query},
            }
        )
        return result["ranker"]["documents"]
