import os

import boto3
from requests_aws4auth import AWS4Auth

client = boto3.client("opensearch", region_name="ap-northeast-2")

response = client.describe_domain(DomainName="opensearch-document-store")

opensearch_vpc_endpoint = response["DomainStatus"]["Endpoints"]["vpc"]

# AWS 인증 정보 설정
region = "ap-northeast-2"
service = "es"
credentials = boto3.Session().get_credentials()

# AWS4Auth 객체 생성
aws_auth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    region,
    service,
    session_token=credentials.token,
)


def get_mandatory_env(name):
    """
    Reads the env variable, raises an exception if missing.
    """
    if name not in os.environ:
        raise Exception("Missing mandatory ENV variable '%s'" % name)
    return os.environ.get(name)
