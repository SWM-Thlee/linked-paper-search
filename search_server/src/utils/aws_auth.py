import boto3
from config import *
from requests_aws4auth import AWS4Auth

# AWS 인증 정보 설정
region = DEFAULT_REGION
service = "es"
credentials = boto3.Session().get_credentials()
aws_auth = AWS4Auth(
    credentials.access_key,
    credentials.secret_key,
    region,
    service,
    session_token=credentials.token,
)

# OpenSearchDocumentStore VPC 엔드포인트 retreive
client = boto3.client("opensearch", region_name="ap-northeast-2")
response = client.describe_domain(DomainName="opensearch-document-store")
opensearch_vpc_endpoint = response["DomainStatus"]["Endpoints"]["vpc"]
