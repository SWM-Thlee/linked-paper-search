import os
import xml.etree.ElementTree as ET
from typing import List

import boto3
from haystack import Document, Pipeline
from haystack.components.embedders import SentenceTransformersDocumentEmbedder
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.writers import DocumentWriter
from haystack.document_stores.types import DuplicatePolicy
from haystack_integrations.document_stores.opensearch import OpenSearchDocumentStore

OPENSEARCH_ID = os.environ.get("OPENSEARCH_ID", "admin")
OPENSEARCH_PW = os.environ.get("OPENSEARCH_PW", "password")

# local OpenSearch server
document_store = OpenSearchDocumentStore(
    index="new_index9",
    hosts="http://0.0.0.0:9200",
    embedding_dim=1024,
    use_ssl=True,
    verify_certs=False,
    http_auth=(OPENSEARCH_ID, OPENSEARCH_PW),
)


hybrid_indexing = Pipeline()
hybrid_indexing.add_component("cleaner", DocumentCleaner())
hybrid_indexing.add_component(
    "splitter", DocumentSplitter(split_by="sentence", split_length=4)
)
hybrid_indexing.add_component(
    "document_embedder", SentenceTransformersDocumentEmbedder(model="BAAI/bge-m3")
)
hybrid_indexing.add_component(
    "writer",
    DocumentWriter(document_store=document_store, policy=DuplicatePolicy.OVERWRITE),
)

hybrid_indexing.connect("cleaner", "splitter")
hybrid_indexing.connect("splitter", "document_embedder")
hybrid_indexing.connect("document_embedder", "writer")


def download_document_list(s3_key: str) -> List[Document]:
    # 환경 변수에서 S3 키를 받아옴

    bucket_name = os.environ.get("DOCUMENT_BUCKET", "paper-feed")

    # S3에서 데이터 읽기
    s3 = boto3.client("s3", region_name="ap-northeast-2")
    response = s3.get_object(Bucket=bucket_name, Key=s3_key)
    data = response["Body"].read().decode("utf-8")

    return convert_xml_to_document_list(data)


def convert_xml_to_document_list(xml_data: str) -> List[Document]:
    # XML 파싱
    root = ET.fromstring(xml_data)

    # XML 네임스페이스 정의
    ns = {
        "oai": "http://www.openarchives.org/OAI/2.0/",
        "arxiv": "http://arxiv.org/OAI/arXivRaw/",
    }

    # Document 리스트 초기화
    documents = []

    # record 요소들을 순회하면서 데이터를 추출
    for record in root.findall(".//oai:record", ns):
        # 메타데이터 추출
        identifier = record.find(".//oai:identifier", ns).text
        datestamp = record.find(".//oai:datestamp", ns).text
        title = record.find(".//arxiv:title", ns).text
        authors = record.find(".//arxiv:authors", ns).text
        abstract = record.find(".//arxiv:abstract", ns).text.strip()
        categories = record.find(".//arxiv:categories", ns).text

        # comments 필드를 조건부로 추출
        comments_element = record.find(".//arxiv:comments", ns)
        comments = comments_element.text if comments_element is not None else None

        license_element = record.find(".//arxiv:license", ns)
        license_url = license_element.text if license_element is not None else None
        submitter = record.find(".//arxiv:submitter", ns).text

        content = title + "\n\n" + abstract

        # 모든 메타데이터를 저장
        meta = {
            "identifier": identifier,
            "datestamp": datestamp,
            "title": title,
            "abstract": abstract,
            "authors": authors,
            "categories": categories,
            "comments": comments,
            "license": license_url,
            "submitter": submitter,
        }

        # Haystack Document 객체 생성
        doc = Document(content=content, meta=meta)

        # Document 리스트에 추가
        documents.append(doc)
    return documents


def upload_document_open_search(document_list):
    # OpenSearch에 연결

    hybrid_indexing.run({"documents": document_list})
    print(document_store.to_dict())
    print(document_store.count_documents())


# If want to insert test dataset to OpenSearch
# if __name__ == "__main__":
#     for i in range(3,100):
#         s3_key = '01-arxiv-raw-v2/cs/arXivRaw_2024_08_07_{:03d}.xml'.format(i)
#         document_list = download_document_list(s3_key)
#         upload_document_open_search(document_list)
#     pass

# Retrieve documents from OpenSearch

from haystack.components.embedders import SentenceTransformersTextEmbedder
from haystack.components.joiners import DocumentJoiner
from haystack.components.rankers import TransformersSimilarityRanker
from haystack_integrations.components.retrievers.opensearch import (
    OpenSearchBM25Retriever,
    OpenSearchEmbeddingRetriever,
)

# Embedder for user query
text_embedder = SentenceTransformersTextEmbedder(model="BAAI/bge-m3")

# Retrieve documents with embedding retriever
embedding_retriever = OpenSearchEmbeddingRetriever(document_store=document_store)
# Retrieve documents with BM25 retriever
bm25_retriever = OpenSearchBM25Retriever(document_store=document_store)

# Combine results from different retrievers
document_joiner = DocumentJoiner()
# rerank retrieved documents with bm25 and embedding retriever
ranker = TransformersSimilarityRanker(model="BAAI/bge-reranker-v2-m3")

hybrid_retrieval = Pipeline()
hybrid_retrieval.add_component("text_embedder", text_embedder)
hybrid_retrieval.add_component("embedding_retriever", embedding_retriever)
hybrid_retrieval.add_component("bm25_retriever", bm25_retriever)
hybrid_retrieval.add_component("document_joiner", document_joiner)
hybrid_retrieval.add_component("ranker", ranker)

hybrid_retrieval.connect("text_embedder", "embedding_retriever")
hybrid_retrieval.connect("bm25_retriever", "document_joiner")
hybrid_retrieval.connect("embedding_retriever", "document_joiner")
hybrid_retrieval.connect("document_joiner", "ranker")

query = "detect object with traffic image"

result = hybrid_retrieval.run(
    {
        "text_embedder": {"text": query},
        "bm25_retriever": {"query": query},
        "ranker": {"query": query},
    }
)


def pretty_print_results(prediction):
    for doc in prediction["documents"]:
        # print(doc)
        print(doc.meta["title"], "\n", "score: ", doc.score)
        print()


# pretty_print_results(result["ranker"])
print(result["ranker"].keys())
