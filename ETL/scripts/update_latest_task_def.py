import time

import boto3

# AWS 리소스 초기화
batch = boto3.client("batch")

# 필요한 정보 입력
job_queue_name = (
    "DocumentEmbedderJobQueue-KKCDOfYv5SinVEXr"  # 여기서 대기열 이름을 입력
)
latest_job_definition = (
    "DocumentEmbedderBatchJo-75ed40197d68e28:9"  # 최신 작업 정의를 입력
)


def list_pending_jobs(queue_name):
    jobs = []
    response = batch.list_jobs(
        jobQueue=queue_name, jobStatus="RUNNABLE"  # 대기 중인 작업
    )
    jobs.extend(response["jobSummaryList"])

    # 추가 페이지가 있는 경우 페이지네이션 처리
    while "nextToken" in response:
        response = batch.list_jobs(
            jobQueue=queue_name, jobStatus="RUNNABLE", nextToken=response["nextToken"]
        )
        jobs.extend(response["jobSummaryList"])

    return jobs


# 2. 작업 상세 정보 가져오기
def get_job_details(job_id):
    try:
        response = batch.describe_jobs(jobs=[job_id])
        if response["jobs"]:
            return response["jobs"][0]
        else:
            return None
    except Exception as e:
        print(f"Error retrieving job details for {job_id}: {e}")
        return None


# 3. 대기 중인 작업 취소하기
def cancel_job(job_id):
    try:
        batch.terminate_job(jobId=job_id, reason="Updating to latest job definition")
        print(f"Cancelled job {job_id}")
    except Exception as e:
        print(f"Error cancelling job {job_id}: {e}")


# 4. 작업 재제출하기 (환경 변수 포함)
def resubmit_job(
    job_name, job_queue, job_definition, environment_vars, parameters=None
):
    try:
        response = batch.submit_job(
            jobName=job_name,
            jobQueue=job_queue,
            jobDefinition=job_definition,
            containerOverrides={"environment": environment_vars},  # 환경 변수 설정
            parameters=parameters or {},
        )
        print(f"Resubmitted job {response['jobId']} with name {job_name}")
    except Exception as e:
        print(f"Error resubmitting job {job_name}: {e}")


# 5. 기존 작업의 환경 변수를 가져와 재제출
def main():
    # 대기 중인 작업 목록 가져오기
    pending_jobs = list_pending_jobs(job_queue_name)

    if not pending_jobs:
        print("No pending jobs found in the queue.")
        return

    for job in pending_jobs:
        job_id = job["jobId"]
        job_name = job["jobName"]

        # 작업 상세 정보 가져오기
        job_details = get_job_details(job_id)
        if not job_details:
            continue

        # 기존 환경 변수를 가져옴
        container = job_details["container"]
        environment_vars = container.get("environment", [])

        # 환경 변수에 S3_BUCKET_NAME 및 S3_OBJECT_KEY가 존재하는지 확인
        has_s3_bucket = any(env["name"] == "S3_BUCKET_NAME" for env in environment_vars)
        has_s3_object_key = any(
            env["name"] == "S3_OBJECT_KEY" for env in environment_vars
        )

        if not has_s3_bucket or not has_s3_object_key:
            print(
                f"Skipping job {job_id} because it lacks S3_BUCKET_NAME or S3_OBJECT_KEY"
            )
            continue

        # 작업 취소
        cancel_job(job_id)
        time.sleep(0.1)  # 잠시 대기

        # 작업 재제출 (환경 변수 포함)
        # resubmit_job(job_name, job_queue_name, latest_job_definition, environment_vars)


if __name__ == "__main__":
    main()
