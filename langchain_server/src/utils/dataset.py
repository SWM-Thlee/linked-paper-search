import logging
import os
import xml.etree.ElementTree as ET
from typing import Dict

import boto3


def download_dataset(bucket_name, object_key, local_dir="test-datasets"):
    """
    로컬 디렉토리에서 XML 파일을 확인하고, 없으면 S3 버킷에서 다운로드하고 로컬에 저장한 후 문자열로 반환합니다.

    :param bucket_name: S3 버킷 이름
    :param object_key: S3 내 객체의 키 (파일 경로 및 이름)
    :param local_dir: 로컬 디렉토리 경로 (기본값: "datasets")
    :return: XML 파일의 내용을 문자열로 반환
    """
    # 로컬 파일 경로 설정
    local_path = os.path.join(local_dir, object_key.split("/")[-1])

    # 로컬 디렉토리 생성 (존재하지 않으면)
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)

    # 로컬 파일 존재 여부 확인
    if os.path.exists(local_path):
        with open(local_path, "r", encoding="utf-8") as file:
            xml_data = file.read()
        return xml_data
    else:
        # S3 서비스 클라이언트 생성
        s3 = boto3.client("s3")

        try:
            # 버킷에서 객체를 다운로드하고 읽기
            response = s3.get_object(Bucket=bucket_name, Key=object_key)
            logging.info(f"Download {object_key}")
            xml_data = response["Body"].read().decode("utf-8")
            # 로컬 파일로 저장
            with open(local_path, "w", encoding="utf-8") as file:
                file.write(xml_data)

            return xml_data
        except Exception as e:
            print(f"An error occurred while downloading from S3: {str(e)}")
            return None


def parse_xml_to_dict(xml_data) -> Dict:
    # XML 데이터를 파싱합니다.
    root = ET.fromstring(xml_data)

    # 최종 결과를 저장할 딕셔너리
    result = {
        "responseDate": root.find(
            ".//{http://www.openarchives.org/OAI/2.0/}responseDate"
        ).text,
        "request": {
            "verb": root.find(
                ".//{http://www.openarchives.org/OAI/2.0/}request"
            ).attrib.get("verb"),
            "until": root.find(
                ".//{http://www.openarchives.org/OAI/2.0/}request"
            ).attrib.get("until"),
            "from": root.find(
                ".//{http://www.openarchives.org/OAI/2.0/}request"
            ).attrib.get("from"),
            "metadataPrefix": root.find(
                ".//{http://www.openarchives.org/OAI/2.0/}request"
            ).attrib.get("metadataPrefix"),
            "set": root.find(
                ".//{http://www.openarchives.org/OAI/2.0/}request"
            ).attrib.get("set"),
            "url": root.find(".//{http://www.openarchives.org/OAI/2.0/}request").text,
        },
        "records": [],
    }

    # 각 레코드 항목을 파싱합니다.
    for record in root.findall(".//{http://www.openarchives.org/OAI/2.0/}record"):
        header = record.find(".//{http://www.openarchives.org/OAI/2.0/}header")
        metadata = record.find(".//{http://arxiv.org/OAI/arXivRaw/}arXivRaw")
        record_data = {
            "identifier": header.find(
                ".//{http://www.openarchives.org/OAI/2.0/}identifier"
            ).text,
            "datestamp": header.find(
                ".//{http://www.openarchives.org/OAI/2.0/}datestamp"
            ).text,
            "setSpec": header.find(
                ".//{http://www.openarchives.org/OAI/2.0/}setSpec"
            ).text,
            "metadata": {
                "id": metadata.find("{http://arxiv.org/OAI/arXivRaw/}id").text,
                "submitter": metadata.find(
                    "{http://arxiv.org/OAI/arXivRaw/}submitter"
                ).text,
                "title": metadata.find("{http://arxiv.org/OAI/arXivRaw/}title").text,
                "authors": metadata.find(
                    "{http://arxiv.org/OAI/arXivRaw/}authors"
                ).text,
                "abstract": metadata.find(
                    "{http://arxiv.org/OAI/arXivRaw/}abstract"
                ).text.strip(),
            },
        }
        result["records"].append(record_data)

    return result
