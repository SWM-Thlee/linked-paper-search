import os

from haystack_integrations.document_stores.opensearch import OpenSearchDocumentStore
from opensearchpy import RequestsHttpConnection
from utils.aws_auth import aws_auth, opensearch_vpc_endpoint
from utils.logger import log_on_init

index = "new_index9"
timeout = 300
use_ssl = True
verify_certs = True


class OpenSearchInterface(OpenSearchDocumentStore):
    pass


@log_on_init("uvicorn.info")
class AwsOpenSearch(OpenSearchInterface):

    def __init__(
        self,
    ):

        super().__init__(
            hosts=[
                {
                    "host": opensearch_vpc_endpoint,
                    "port": 443,
                }
            ],
            index="test-index",
            http_auth=aws_auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
        )


class LocalOpenSearch(OpenSearchInterface):
    def __init__(
        self,
    ):
        OPENSEARCH_ID = os.environ.get("OPENSEARCH_ID", "admin")
        OPENSEARCH_PW = os.environ.get("OPENSEARCH_PW", "password")

        super().__init__(
            index="new_index9",
            hosts="http://0.0.0.0:9200",
            embedding_dim=1024,
            use_ssl=True,
            http_auth=(OPENSEARCH_ID, OPENSEARCH_PW),
        )
