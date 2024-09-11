import os

import boto3
from haystack_integrations.document_stores.opensearch import OpenSearchDocumentStore
from opensearchpy import RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from utils.logger import log_on_init


class OpenSearchDocumentStore(OpenSearchDocumentStore):
    pass


@log_on_init()
class AwsOpenSearch(OpenSearchDocumentStore):

    def __init__(
        self,
        index="new_index9",
        timeout=900,
        use_ssl=True,
        verify_certs=True,
        embedding_dim=1024,
        DEFAULT_REGION="ap-northeast-2",
    ):
        credentials = boto3.Session().get_credentials()
        aws_auth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            DEFAULT_REGION,
            "es",
            session_token=credentials.token,
        )

        # OpenSearchDocumentStore VPC 엔드포인트 retreive
        client = boto3.client("opensearch", region_name="ap-northeast-2")
        response = client.describe_domain(DomainName="opensearch-document-store")
        opensearch_vpc_endpoint = response["DomainStatus"]["Endpoints"]["vpc"]
        super().__init__(
            hosts=[
                {
                    "host": opensearch_vpc_endpoint,
                    "port": 443,
                }
            ],
            index=index,
            http_auth=aws_auth,
            use_ssl=use_ssl,
            timeout=timeout,
            embedding_dim=embedding_dim,
            verify_certs=verify_certs,
            connection_class=RequestsHttpConnection,
        )


@log_on_init()
class LocalOpenSearch(OpenSearchDocumentStore):
    def __init__(
        self,
        index="new_index9",
        use_ssl=True,
        embedding_dim=1024,
    ):
        OPENSEARCH_ID = os.environ.get("OPENSEARCH_ID", "admin")
        OPENSEARCH_PW = os.environ.get("OPENSEARCH_PW", "password")

        super().__init__(
            index=index,
            hosts="http://0.0.0.0:9200",
            embedding_dim=embedding_dim,
            use_ssl=use_ssl,
            http_auth=(OPENSEARCH_ID, OPENSEARCH_PW),
        )
