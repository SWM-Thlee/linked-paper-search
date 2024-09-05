import json
import os
import re

import boto3

batch_client = boto3.client("batch")


def handler(event, context):
    """
    S3에 파일이 추가될 때 Lambda가 트리거되어 AWS Batch 작업을 제출
    """
    print(f"Received event: {json.dumps(event)}")

    # S3 이벤트로부터 버킷 이름과 파일 키 추출
    for record in event["Records"]:
        bucket_name = record["s3"]["bucket"]["name"]
        object_key = record["s3"]["object"]["key"]
        print(f"New object detected: {object_key} in bucket: {bucket_name}")

        # 파일 확장자가 xml인 경우에만 Batch 작업 제출
        if object_key.lower().endswith(".xml"):
            print(f"XML file detected: {object_key}, submitting batch job.")
            response = submit_batch_job(bucket_name, object_key)
            print(f"Batch job submitted: {response}")
        else:
            print(
                f"File is not an XML file: {object_key}, skipping batch job submission."
            )


def submit_batch_job(bucket_name, object_key):
    """
    AWS Batch 작업 제출
    """
    job_queue = os.environ["BATCH_JOB_QUEUE"]
    job_definition = os.environ["BATCH_JOB_DEFINITION"]

    job_name = generate_valid_job_name(object_key)
    # AWS Batch 작업 제출
    response = batch_client.submit_job(
        jobName=job_name,
        jobQueue=job_queue,
        jobDefinition=job_definition,
        containerOverrides={
            "environment": [
                {"name": "S3_BUCKET_NAME", "value": bucket_name},
                {"name": "S3_OBJECT_KEY", "value": object_key},
            ],
        },
    )

    return response


def generate_valid_job_name(object_key):
    """
    S3 오브젝트 키에서 유효한 Batch Job 이름 생성
    AWS Batch Job 이름 패턴: ^[^:|]*$ (콜론과 세로선을 포함할 수 없음)
    특수 문자를 제거하거나 밑줄로 변환.
    """
    # 특수 문자를 제거하고 유효한 이름 생성
    job_name = re.sub(r"[^a-zA-Z0-9-_]+", "_", object_key)

    # Job 이름이 너무 길면 앞부분만 사용 (최대 128자)
    return job_name[:128]
