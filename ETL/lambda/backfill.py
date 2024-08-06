# lambda/backfill.py

import datetime
import json
import logging
import os
from time import sleep

import boto3

# 로거 설정
logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    glue_client = boto3.client("glue")
    glue_job_name = os.environ["GLUE_JOB_NAME"]

    # 현재 연도와 분기 계산
    current_year = datetime.datetime.now().year
    current_quarter = (datetime.datetime.now().month - 1) // 3 + 1

    categories = ["cs"]  # 사용할 카테고리 리스트

    for category in categories:
        for year in range(2007, current_year + 1):  # 2007년부터 현재 연도까지
            # 연도가 현재 연도일 때, 현재 분기까지만 반복
            if year == current_year:
                end_quarter = current_quarter
            else:
                end_quarter = 4  # 그 외의 경우는 모든 분기 (1, 2, 3, 4)

            for quarter in range(1, end_quarter + 1):  # 분기 반복
                arguments = {
                    "--category": category,
                    "--year": str(year),
                    "--quarter": str(quarter),
                }

                # Glue Job 시작
                try:
                    response = glue_client.start_job_run(
                        JobName=glue_job_name, Arguments=arguments
                    )
                    logger.info(
                        f"Started Glue job {glue_job_name} for {category}, {year}, Quarter: {quarter}, JobRunId: {response['JobRunId']}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to start Glue job for {category}, {year}, Quarter: {quarter}. Error: {e}"
                    )

                sleep(5)  # Glue Job 간 간격을 두기 위해 슬립

    return {"message": "Backfill started!"}
