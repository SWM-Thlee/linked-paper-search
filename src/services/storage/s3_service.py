import boto3

class S3Service:
    def __init__(self, bucket_name):
        self.bucket_name = bucket_name
        self.__s3_client = boto3.client('s3')

    def put_object(self, key, data):
        self.__s3_client.put_object(Body=data, Bucket=self.bucket_name, Key=key)

    def get_object(self, key):
        response = self.__s3_client.get_object(Bucket=self.bucket_name, Key=key)
        return response['Body'].read().decode('utf-8')
