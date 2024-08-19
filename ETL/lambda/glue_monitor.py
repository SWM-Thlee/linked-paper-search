import json
import os

import urllib3
from utils.secret_manager import get_secret

http = urllib3.PoolManager()


def handler(event, context):
    webhook_url = get_secret(os.environ["SLACK_WEBHOOK_SECRET_NAME"])
    job_name = event["detail"]["jobName"]
    state = event["detail"]["state"]

    # 파라미터를 event에서 가져오기
    job_run_id = event["detail"].get("jobRunId", "N/A")
    arguments = event["detail"].get("arguments", {})

    # 메시지 구성
    message = {
        "text": f"Glue Job `{job_name}` has `{state}`.\nJob Run ID: `{job_run_id}`\nArguments: {json.dumps(arguments)}"
    }

    # Slack으로 메시지 전송
    response = http.request(
        "POST",
        webhook_url,
        body=json.dumps(message),
        headers={"Content-Type": "application/json"},
    )

    return {"statusCode": 200, "body": json.dumps(response.data.decode("utf-8"))}
