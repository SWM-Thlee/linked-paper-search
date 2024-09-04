import xml.etree.ElementTree as ET
from typing import List

import boto3
from haystack import Document


def download_document_list(bucket_name: str, s3_key: str) -> List[Document]:
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
