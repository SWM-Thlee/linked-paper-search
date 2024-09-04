import json
import os
from datetime import datetime, timedelta

import boto3


def handler(event, context):
    # AWS services client setup
    s3_client = boto3.client("s3")
    glue_client = boto3.client("glue")
    glue_job_name = os.environ["GLUE_JOB_NAME"]
    bucket_name = os.environ["METADATA_BUCKET"]  # S3 bucket where metadata is stored

    # Retrieve category from event or default
    category = event.get("category", "cs")

    metadata_key = (
        f"01-arxiv-raw-v2/{category}/metadata.json"  # Key for the metadata file in S3
    )

    # Fetch the last collection date from S3 metadata
    response = s3_client.get_object(Bucket=bucket_name, Key=metadata_key)
    metadata_content = response["Body"].read().decode("utf-8")
    metadata = json.loads(metadata_content)
    last_updated = metadata.get("LastUpdated", datetime.now().strftime("%Y-%m-%d"))

    # Calculate the next start date from the last collection date
    last_collection_date = datetime.strptime(last_updated, "%Y-%m-%d")
    start_date = (last_collection_date + timedelta(days=1)).strftime("%Y-%m-%d")

    print(f"Starting Glue job {glue_job_name} with start date {start_date}")
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
