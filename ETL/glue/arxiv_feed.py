import calendar
import datetime

# logger 설정 필요시 사용
import json
import logging
import sys
import time
import urllib.request
from xml.etree import ElementTree as ET

import boto3
from awsglue.utils import getResolvedOptions

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

base_url = "http://export.arxiv.org/oai2?"
target_bucket = "paper-feed"
s3_client = boto3.client("s3")
max_retries = 10


# Use the current date for naming the S3 key
current_date = datetime.datetime.now()
current_year = current_date.year
current_month = current_date.month
current_day = current_date.day

# Metadata for the dataset
metadata = {
    "LastUpdated": f"{current_year}-{current_month:02d}-{current_day:02d}",
    "Category": "cs",
}


def export_arxiv_papers_by_start_date(category: str, start_date: str):
    """
    AWS Glue Job을 위한 함수로서, 주어진 시작 날짜를 기준으로 논문 데이터를 수집하여 S3에 저장.

    Args:
        category (str): 수집할 논문 카테고리 (cs, bio 등)
        start_date (str): 수집할 논문의 시작 날짜 (YYYY-MM-DD 형식)
    """
    # 시작 날짜에서 년도 및 월을 추출
    start_date_dt = datetime.datetime.strptime(start_date, "%Y-%m-%d")
    year = start_date_dt.year
    month = start_date_dt.month
    day = start_date_dt.day

    # OAI 요청 URL 구성
    query_params = f"verb=ListRecords&set={category}&metadataPrefix=arXivRaw&from={year}-{month:02d}-{day:02d}"
    url = base_url + query_params

    retry_count = 0
    page = 1
    while retry_count < max_retries:
        try:
            response = urllib.request.urlopen(url)
            if response.getcode() != 200:
                logger.warning("Response code is not 200. Retrying...")
                retry_count += 1
                time.sleep(5)
                continue
            data = response.read().decode("utf-8")
            tree = ET.fromstring(data)

            # Save the fetched data to S3 bucket
            s3_key = f"01-arxiv-raw-v2/{category}/arXivRaw_{current_year}_{current_month:02d}_{current_day:02d}_{page:03d}.xml"
            s3_client.put_object(Body=data, Bucket=target_bucket, Key=s3_key)
            logger.info(f"Saved {s3_key} to S3 bucket.")

            page += 1

            token = tree.find(
                ".//{http://www.openarchives.org/OAI/2.0/}resumptionToken"
            )
            if token is not None and token.text:
                query_params = f"verb=ListRecords&resumptionToken={token.text}"
                url = base_url + query_params
            else:
                break
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            logger.info("Retrying...")
            retry_count += 1
            if retry_count >= max_retries:
                logger.error("Maximum retry limit reached, failing the function.")
                raise Exception("Maximum retry limit reached, function failed.")
            time.sleep(10)

    metadata["LastUpdatedFile"] = s3_key
    metadata_json = json.dumps(metadata, indent=4)
    metadata_key = f"01-arxiv-raw-v2/{category}/metadata.json"

    s3_client.put_object(Body=metadata_json, Bucket=target_bucket, Key=metadata_key)


# Glue Job 실행 시 인수 받기
args = getResolvedOptions(sys.argv, ["category", "start_date"])

# 함수 실행
export_arxiv_papers_by_start_date(
    category=args["category"], start_date=args["start_date"]
)
