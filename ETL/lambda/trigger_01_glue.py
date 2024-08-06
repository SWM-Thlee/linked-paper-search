import os

import boto3


def handler(event, context):
    glue_client = boto3.client("glue")
    glue_job_name = os.environ["GLUE_JOB_NAME"]

    # 전달할 매개변수 정의
    arguments = {
        "--category": event.get("category", "cs"),
        "--year": str(event.get("year", 2024)),
        "--quarter": str(event.get("quarter", 3)),
    }

    try:
        response = glue_client.start_job_run(
            JobName=glue_job_name, Arguments=arguments  # Glue Job에 매개변수 전달
        )
        return {
            "statusCode": 200,
            "body": f"Glue job {glue_job_name} started with run ID {response['JobRunId']}",
        }
    except Exception as e:
        return {"statusCode": 500, "body": str(e)}
