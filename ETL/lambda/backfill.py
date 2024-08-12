import os

import boto3


def handler(event, context):
    # AWS services client setup
    glue_client = boto3.client("glue")
    glue_job_name = os.environ["GLUE_JOB_NAME"]

    # Retrieve category from event or default
    category = event.get("category", "cs")
    start_date = event.get("start_date")  # Backfill 시작 날짜 지정안하면 Exception 발생

    # Define the parameters to pass to the Glue job
    arguments = {"--category": category, "--start_date": start_date}

    try:
        # Start the Glue job with the parameters
        response = glue_client.start_job_run(JobName=glue_job_name, Arguments=arguments)
        return {
            "statusCode": 200,
            "body": f"Glue job {glue_job_name} started with run ID {response['JobRunId']}. Start date set to {start_date}",
        }
    except Exception as e:
        # Return an error response if the job fails to start
        return {
            "statusCode": 500,
            "body": f"Failed to start Glue job {glue_job_name}. Error: {str(e)}",
        }
