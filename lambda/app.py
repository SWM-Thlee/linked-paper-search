import datetime
import json
from time import sleep

import boto3
from chalice import Chalice
from chalicelib.collect_data_01.arxiv_feed import export_arxiv_papers_by_quarter
from chalicelib.config.logger_config import logger

app = Chalice(app_name="paper-pipeline")

categories = ["cs"]


@app.lambda_function()
def backfill_raw_papers(event, context):
    """Backfill raw papers from 2007 to the current year and quarter
    feed_papers_by_quarter 함수를 호출하여 2007년부터 현재 연도까지의 분기별 논문 데이터를 수집

    Args:
        event: AWS Lambda Event
        context: AWS Lambda Context

    Returns:
        dict: 시작 메시지를 포함한 딕셔너리
    """
    lambda_client = boto3.client("lambda")

    # 현재 연도와 분기 계산
    current_year = datetime.datetime.now().year
    current_quarter = (datetime.datetime.now().month - 1) // 3 + 1

    for category in categories:
        for year in range(2007, current_year + 1):  # 2007년부터 현재 연도까지
            # 연도가 현재 연도일 때, 현재 분기까지만 반복
            if year == current_year:
                end_quarter = current_quarter
            else:
                end_quarter = 4  # 그 외의 경우는 모든 분기 (1, 2, 3, 4)

            for quarter in range(1, end_quarter + 1):  # 분기 반복
                payload = {
                    "category": category,
                    "year": year,
                    "quarter": quarter,  # 분기 정보를 payload에 추가
                }
                # Lambda 함수 비동기 호출
                lambda_client.invoke(
                    FunctionName="paper-pipeline-dev-feed_papers_by_quarter",
                    InvocationType="Event",
                    Payload=json.dumps(payload),
                )
                logger.info(
                    f"Invoked feed_papers_by_quarter for {category}, {year}, Quarter: {quarter}"
                )
                sleep(5)

    return {"message": "Backfill started!"}


@app.lambda_function()
def feed_papers_by_quarter(event, context):
    """
    Feed papers by quarter. This function is triggered to fetch and process data
    for a specific quarter of a specified year.

    Args:
        event (dict): Request payload containing 'category', 'year', and 'quarter'.
        context: Lambda context object (unused in the function).

    Returns:
        dict: A message indicating the completion or failure of the data processing.
    """
    category: str = event["category"]
    year: int = event.get("year", datetime.datetime.now().year)

    current_month = datetime.datetime.now().month
    current_quarter = (current_month - 1) // 3 + 1
    quarter: int = event.get("quarter", current_quarter)

    export_arxiv_papers_by_quarter(category, year, quarter)
    return {"message": "Done!"}
