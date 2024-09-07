import json

import boto3

# AWS Boto3 클라이언트 생성
batch = boto3.client("batch")

# Job Queue 이름 설정
job_queue_name = "DocumentEmbedderJobQueue"

# Job Queue ARN 가져오기
response = batch.describe_job_queues()
job_queue = None

# DocumentEmbedderJobQueue가 포함된 Job Queue 찾기
for queue in response["jobQueues"]:
    if job_queue_name in queue["jobQueueArn"]:
        job_queue = queue
        break

if job_queue is None:
    print(f"Error: Job Queue with '{job_queue_name}' not found. Exiting...")
    exit(1)

job_queue_id = job_queue["jobQueueArn"].split("/")[-1]

# 실패한 작업 목록 가져오기
failed_jobs = batch.list_jobs(jobQueue=job_queue_id, jobStatus="FAILED")[
    "jobSummaryList"
]

if not failed_jobs:
    print("No failed jobs found.")
    exit(0)

# 실패한 작업들 다시 제출
for job in failed_jobs:
    job_id = job["jobId"]

    # 작업에 대한 자세한 정보 가져오기
    job_description = batch.describe_jobs(jobs=[job_id])["jobs"][0]
    job_name = job_description["jobName"]
    job_definition = job_description["jobDefinition"]
    # job_definition = "DocumentEmbedderBatchJo-75ed40197d68e28:6"

    # 이전 작업의 환경 변수 추출하기
    environment_vars = job_description["container"]["environment"]

    # 작업 다시 제출
    print(f"Submitting job {job_name} with job ID {job_id}")

    # 작업 다시 제출
    response = batch.submit_job(
        jobName=job_name,
        jobQueue=job_queue_id,
        jobDefinition=job_definition,
        containerOverrides={"environment": environment_vars},
    )

    # 제출된 작업의 정보를 출력
    print(
        json.dumps(
            {"jobName": response["jobName"], "jobId": response["jobId"]}, indent=4
        )
    )
