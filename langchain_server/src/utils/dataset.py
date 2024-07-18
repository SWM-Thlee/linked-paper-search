import xml.etree.ElementTree as ET

import boto3


def download_dataset_from_s3(bucket_name, object_key):
    """
    S3 버킷에서 XML 파일을 다운로드하고 문자열로 반환합니다.

    :param bucket_name: S3 버킷 이름
    :param object_key: S3 내 객체의 키 (파일 경로 및 이름)
    :return: 다운로드된 XML 파일의 내용을 문자열로 반환
    """
    # S3 서비스 클라이언트 생성
    s3 = boto3.client("s3")

    try:
        # 버킷에서 객체를 다운로드하고 읽기
        response = s3.get_object(Bucket=bucket_name, Key=object_key)
        xml_data = response["Body"].read().decode("utf-8")
        return xml_data
    except Exception as e:
        print(f"An error occurred while downloading from S3: {str(e)}")
        return None


def parse_xml_to_dict(xml_data):
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
