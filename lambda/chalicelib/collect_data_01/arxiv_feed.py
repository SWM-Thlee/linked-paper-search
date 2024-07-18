import calendar
import datetime
import time
import urllib.request
from xml.etree import ElementTree as ET

import boto3

from ..config.logger_config import logger

base_url = "http://export.arxiv.org/oai2?"
target_bucket = "paper-feed"
s3_client = boto3.client("s3")
max_retries = 10


def export_arxiv_papers_by_quarter(category: str, year=None | int, quarter=None | int):
    """Lambda 호출 시간을 고려하여 해당 년도의 분기 데이터를 수집하는 함수
    주의: 데이터를 수집하는 데 5분 이상 소요될 수 있음.
    OAI datastamp를 기준으로 년/분기 확인 (datastamp는 KST 12:00 am 기준으로 변경됨) => 데이터 수집 시 해당 시간 전에 완료해야 함.

    Args:
        category (str): 수집할 논문 카테고리 (cs, bio ...)
        year (int, optional): 수집할 논문의 년도. Defaults to current year.
        quarter (int, optional): 수집할 분기 (1 to 4). Defaults to current quarter.
    """
    now = datetime.datetime.now()
    if year is None:
        year = now.year
    if quarter is None:
        quarter = (now.month - 1) // 3 + 1

    quarter_months = {1: (1, 3), 2: (4, 6), 3: (7, 9), 4: (10, 12)}
    start_month, end_month = quarter_months[quarter]
    start_day = 1
    end_day = calendar.monthrange(year, end_month)[1]  # 해당 분기 마지막 달의 마지막 일

    # OAI 요청 URL 구성
    query_params = f"verb=ListRecords&set={category}&metadataPrefix=arXivRaw&from={year}-{start_month:02d}-{start_day:02d}&until={year}-{end_month:02d}-{end_day:02d}"
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
            s3_key = (
                f"01-arxiv-raw/{category}/arXivRaw_{year}-Q{quarter}_{page:03d}.xml"
            )
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


if __name__ == "__main__":
    export_arxiv_papers_by_quarter("cs")
