import os
import time

from haystack import Document, Pipeline
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.writers import DocumentWriter
from haystack.document_stores.types import DuplicatePolicy
from haystack_integrations.document_stores.opensearch import OpenSearchDocumentStore
from opensearchpy import RequestsHttpConnection
from requests.exceptions import HTTPError

from .utils import aws_auth, opensearch_vpc_endpoint

embedding_model = "BAAI/bge-m3"
index = "new_paper_document_index"

opensearch_endpoint = (
    opensearch_vpc_endpoint  # 같은 subnet에 있는 OpenSearch vpc 엔드포인트
)

print(f"OpenSearch endpoint: {opensearch_endpoint}")
# OpenSearchDocumentStore 설정
document_store = OpenSearchDocumentStore(
    hosts=[
        {
            "host": opensearch_endpoint,
            "port": 443,
        }
    ],
    index=index,
    http_auth=aws_auth,
    timeout=900,
    embedding_dim=1024,  # BAAI/bge-m3 output vector dimension
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection,  # 중요: RequestsHttpConnection을 사용해야만 OpenSearchDocumentStore가 정상적으로 작동함
)

# 모델을 다운로드할 로컬 경로
# 로컬 모델 경로 설정 (Docker 이미지 내부 경로)
local_embedding_model_path = os.getenv("BGE_M3_MODEL_PATH", "/app/models/bge-m3")

# Pipeline 설정
hybrid_indexing = Pipeline()
hybrid_indexing.add_component("cleaner", DocumentCleaner())
hybrid_indexing.add_component(
    "splitter", DocumentSplitter(split_by="sentence", split_length=4)
)
hybrid_indexing.add_component(
    "document_embedder",
    SentenceTransformersDocumentEmbedder(model=embedding_model),
)
hybrid_indexing.add_component(
    "writer",
    DocumentWriter(document_store=document_store, policy=DuplicatePolicy.OVERWRITE),
)

hybrid_indexing.connect("cleaner", "splitter")
hybrid_indexing.connect("splitter", "document_embedder")
hybrid_indexing.connect("document_embedder", "writer")

hybrid_indexing.warm_up()


def write_documents_with_retry(
    documents,
    pipeline=hybrid_indexing,
    batch_size=50,
    max_retries=5,
    initial_backoff=1,
):
    # 문서를 배치로 나눕니다.
    #  IO job인 document write를 비동기 처리할까??
    for i in range(0, len(documents), batch_size):
        batch = documents[i : i + batch_size]
        for attempt in range(max_retries):
            try:
                pipeline.run({"documents": batch})
                print(f"Successfully indexed batch {i // batch_size + 1}")
                break
            except HTTPError as e:
                # OpenSearch가 429 Too Many Requests를 반환하면, 지수 백오프를 적용하여 재시도합니다.
                if e.response.status_code == 429:
                    wait_time = initial_backoff * 2**attempt
                    print(
                        f"429 Too Many Requests - Retry {attempt + 1}/{max_retries} after {wait_time} seconds"
                    )
                    time.sleep(wait_time)  # 지수 백오프 적용
                else:
                    raise e
        else:
            print("Max retries exceeded, document indexing failed for batch")
