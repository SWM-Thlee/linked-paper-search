import os

from source.document import download_document_list
from source.pipeline import write_documents_with_retry
from source.utils import get_mandatory_env


def main():
    """
    Batch job execution entry point script.
    Environemnt variables set by the AWS CDK infra code.
    """
    bucket_name = get_mandatory_env("S3_BUCKET_NAME")
    s3_object_key = get_mandatory_env("S3_OBJECT_KEY")
    documents = download_document_list(bucket_name, s3_object_key)
    write_documents_with_retry(documents)


if __name__ == "__main__":
    main()
