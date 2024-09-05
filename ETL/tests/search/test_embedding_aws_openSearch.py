import boto3
from haystack import Document
from haystack.document_stores.types import DuplicatePolicy
from haystack_integrations.components.retrievers.opensearch import (
    OpenSearchBM25Retriever,
)
from haystack_integrations.document_stores.opensearch import OpenSearchDocumentStore
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth

# AWS 인증 정보 설정
region = "ap-northeast-2"
service = "es"
credentials = boto3.Session().get_credentials()
aws_auth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    region,
    service,
    session_token=credentials.token,
)

# OpenSearchDocumentStore 설정
document_store = OpenSearchDocumentStore(
    hosts=[
        {
            "host": "search-test-brxvf4xn4itcbmpiagf7t76ncu.ap-northeast-2.es.amazonaws.com",
            "port": 443,
        }
    ],
    index="test-index",
    http_auth=aws_auth,
    timeout=300,
    use_ssl=True,
    verify_certs=True,
    # 중요: RequestsHttpConnection을 사용해야만 OpenSearchDocumentStore가 정상적으로 작동함
    # 기본값인 Urllib3HttpConnection을 사용하면 오류 발생
    # https://opensearch-project.github.io/opensearch-py/api-ref/clients/opensearch_client.html
    connection_class=RequestsHttpConnection,
)

# 문서 삽입
doc = Document(content="This is a sample document for AWS OpenSearch integration.")
document_store.write_documents([doc], policy=DuplicatePolicy.OVERWRITE)

# 검색
retriever = OpenSearchBM25Retriever(document_store=document_store)
results = retriever.run(query="sample", top_k=10)

print(results)
for result in results:
    print(result)
