import os

import boto3
from haystack_integrations.document_stores.opensearch import OpenSearchDocumentStore
from opensearchpy import RequestsHttpConnection
from opensearchpy.exceptions import AuthorizationException
from requests_aws4auth import AWS4Auth
from utils.logger import log_on_init, logger


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
        self.DEFAULT_REGION = DEFAULT_REGION
        self.index = index
        self.timeout = timeout
        self.use_ssl = use_ssl
        self.verify_certs = verify_certs
        self.embedding_dim = embedding_dim

        # OpenSearchDocumentStore VPC 엔드포인트 retrieve
        client = boto3.client("opensearch", region_name=self.DEFAULT_REGION)
        response = client.describe_domain(DomainName="opensearch-document-store")
        opensearch_vpc_endpoint = response["DomainStatus"]["Endpoints"]["vpc"]

        super().__init__(
            hosts=[
                {
                    "host": opensearch_vpc_endpoint,
                    "port": 443,
                }
            ],
            index=self.index,
            use_ssl=self.use_ssl,
            timeout=self.timeout,
            embedding_dim=self.embedding_dim,
            verify_certs=self.verify_certs,
            connection_class=RequestsHttpConnection,
            return_embedding=True,
        )
        self.update_auth_credentials()

    def update_auth_credentials(self):
        """
        자격 증명을 새로고침하여 AWS4Auth 객체를 갱신하는 함수
        """
        credentials = boto3.Session().get_credentials()
        self.aws_auth = AWS4Auth(
            region=self.DEFAULT_REGION,
            service="es",
            refreshable_credentials=credentials,
        )
        print(f"Updated AWS4Auth credentials: {self.aws_auth.date}")

        # 기존 연결에 새로운 자격 증명 갱신
        self._http_auth = self.aws_auth

    def _search_documents(self, *args, **kwargs):
        """
        OpenSearchDocumentStore의 _search_documents 실행중 403 AuthorizationException catch
        """
        try:
            # 상속받은 메서드 로직을 그대로 실행
            return super()._search_documents(*args, **kwargs)
        except AuthorizationException as e:
            if e.status_code == 403:
                logger.warning(
                    "403 AuthorizationException: Refreshing AWS credentials."
                )
                self._client = None  # auth 재설정을 위한 클라이언트 초기화
                self.update_auth_credentials()
                # 자격 증명 갱신 후 메서드 다시 실행
                return super()._search_documents(*args, **kwargs)
            else:
                # 다른 예외는 다시 raise
                raise e


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
            return_embedding=True,
        )
