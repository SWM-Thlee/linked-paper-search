import os

from haystack_integrations.document_stores.opensearch import OpenSearchDocumentStore
from opensearchpy import RequestsHttpConnection
from utils.aws_auth import aws_auth, opensearch_vpc_endpoint
from utils.logger import log_on_init

index = "new_index9"
timeout = 900
use_ssl = True
verify_certs = True
embedding_dim = 1024


class OpenSearchDocumentStore(OpenSearchDocumentStore):
    pass


@log_on_init("uvicorn.info")
class AwsOpenSearch(OpenSearchDocumentStore):

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
            index=index,
            http_auth=aws_auth,
            use_ssl=use_ssl,
            timeout=timeout,
            embedding_dim=embedding_dim,
            verify_certs=verify_certs,
            connection_class=RequestsHttpConnection,
        )


@log_on_init("uvicorn.info")
class LocalOpenSearch(OpenSearchDocumentStore):
    def __init__(
        self,
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
