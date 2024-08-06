from aws_cdk import Aws, Duration, Stack
from aws_cdk import aws_glue as glue
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_s3 as s3
from constructs import Construct


class EtlStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # 기존 S3 버킷을 참조
        bucket_name = "etl-glue-script"
        glue_bucket = s3.Bucket.from_bucket_name(
            self, "GlueScriptsBucket", bucket_name=bucket_name
        )

        # Glue IAM 역할 생성
        glue_role = iam.Role(
            self,
            "GlueJobRole",
            assumed_by=iam.ServicePrincipal("glue.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSGlueServiceRole"
                )
            ],
        )

        # Glue 스크립트를 읽기 위한 S3 버킷 권한 부여
        glue_bucket.grant_read(glue_role)

        # paper-feed 버킷에 대한 쓰기 권한 부여
        paper_feed_bucket_name = "paper-feed"
        paper_feed_bucket = s3.Bucket.from_bucket_name(
            self, "PaperFeedBucket", bucket_name=paper_feed_bucket_name
        )
        paper_feed_bucket.grant_put(glue_role)  # 업로드 권한 부여

        # Glue Job 생성
        glue_job = glue.CfnJob(
            self,
            "ArxivFeedGlueJob",
            role=glue_role.role_arn,
            command={
                "name": "glueetl",
                "scriptLocation": glue_bucket.s3_url_for_object(
                    "scripts/arxiv_feed.py"
                ),
            },
            default_arguments={
                "--TempDir": glue_bucket.s3_url_for_object("temporary/"),
                "--job-language": "python",
            },
            glue_version="2.0",
            max_retries=3,
        )

        # Glue Job ARN 수동 구성
        glue_job_arn = f"arn:aws:glue:{Aws.REGION}:{Aws.ACCOUNT_ID}:job/{glue_job.ref}"

        # Glue Job을 트리거하는 Lambda 함수 생성
        trigger_lambda = _lambda.Function(
            self,
            "trigger01GlueJob",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="trigger_01_glue.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "GLUE_JOB_NAME": glue_job.ref,
            },
            timeout=Duration.minutes(5),
        )

        # Lambda가 Glue Job을 시작할 수 있도록 권한 부여
        glue_role.grant_pass_role(trigger_lambda)
        trigger_lambda.add_to_role_policy(
            iam.PolicyStatement(actions=["glue:StartJobRun"], resources=[glue_job_arn])
        )

        # Backfill Lambda 함수 생성
        backfill_lambda = _lambda.Function(
            self,
            "BackfillLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="backfill.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "GLUE_JOB_NAME": glue_job.ref,
            },
            timeout=Duration.minutes(15),
        )

        # Backfill Lambda에 필요한 Glue Job 시작 권한 부여
        backfill_lambda.add_to_role_policy(
            iam.PolicyStatement(actions=["glue:StartJobRun"], resources=[glue_job_arn])
        )
