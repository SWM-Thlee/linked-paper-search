import aws_cdk.aws_events as events
import aws_cdk.aws_events_targets as targets
from aws_cdk import Aws, Duration, Stack
from aws_cdk import aws_glue as glue
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_secretsmanager as secretsmanager
from constructs import Construct

glue_bucket_name = "etl-glue-script"
paper_feed_bucket_name = "paper-feed"


class EtlStack(Stack):

    def create_feed_layer(self):
        """
        Layer 01: Glue Job
        TODO 1: region 지정 (default: northeast-2)
        """

        glue_bucket = s3.Bucket.from_bucket_name(
            self, "GlueScriptsBucket", bucket_name=glue_bucket_name
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
            glue_version="4.0",
            max_retries=3,
        )

        # Glue Job ARN 수동 구성
        glue_job_arn = f"arn:aws:glue:{Aws.REGION}:{Aws.ACCOUNT_ID}:job/{glue_job.ref}"

        # Glue Job 완료 이벤트 규칙 생성
        glue_finish_event_rule = events.Rule(
            self,
            "GlueJobCompletionRule",
            event_pattern={
                "source": ["aws.glue"],
                "detail_type": ["Glue Job State Change"],
                "detail": {"jobName": [glue_job.ref], "state": ["SUCCEEDED", "FAILED"]},
            },
        )

        # Secrets Manager에서 Secret 참조
        glue_slack_webhook_url = secretsmanager.Secret.from_secret_name_v2(
            self, "SlackWebhookSecret", "GlueSlackWebhookURL"
        )

        # Slack 알림 Lambda 함수 생성
        lambda_slack_notifier = _lambda.Function(
            self,
            "SlackNotificationFunction",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="glue_monitor.handler",
            code=_lambda.Code.from_asset("lambda"),  # Lambda 코드가 포함된 경로
            environment={
                "SLACK_WEBHOOK_SECRET_NAME": glue_slack_webhook_url.secret_name
            },
            timeout=Duration.minutes(1),
        )

        # Lambda에 필요한 권한 추가
        lambda_slack_notifier.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "logs:CreateLogGroup",
                    "logs:CreateLogStream",
                    "logs:PutLogEvents",
                ],
                resources=["*"],
            )
        )

        glue_slack_webhook_url.grant_read(lambda_slack_notifier)
        glue_finish_event_rule.add_target(targets.LambdaFunction(lambda_slack_notifier))

        # Glue Job을 트리거하는 Lambda 함수 생성
        trigger_lambda = _lambda.Function(
            self,
            "trigger01GlueJob",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="trigger_01_glue.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "GLUE_JOB_NAME": glue_job.ref,
                "METADATA_BUCKET": paper_feed_bucket_name,
            },
            timeout=Duration.minutes(5),
        )
        # Lambda가 paper-feed 버킷을 읽을 수 있도록 권한 부여
        paper_feed_bucket.grant_read(trigger_lambda.role)

        # Lambda가 Glue Job을 시작할 수 있도록 권한 부여
        glue_role.grant_pass_role(trigger_lambda)
        trigger_lambda.add_to_role_policy(
            iam.PolicyStatement(actions=["glue:StartJobRun"], resources=[glue_job_arn])
        )

        # 매주 금요일 EST 오후 1시에 실행되도록 CloudWatch Event Rule 생성
        weekly_trigger_rule = events.Rule(
            self,
            "TriggerLambdaEveryFriday1PM",
            schedule=events.Schedule.cron(
                minute="0",
                hour="18",  # EST 오후 1시 = UTC 오후 6시
                week_day="FRI",
            ),
        )

        # Lambda 함수를 이벤트 규칙의 타겟으로 추가
        weekly_trigger_rule.add_target(targets.LambdaFunction(trigger_lambda))

        # Backfill Lambda 함수 생성
        backfill_lambda = _lambda.Function(
            self,
            "Backfill01",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="backfill.handler",
            code=_lambda.Code.from_asset("lambda"),
            environment={
                "GLUE_JOB_NAME": glue_job.ref,
                "METADATA_BUCKET": paper_feed_bucket_name,
            },
            timeout=Duration.minutes(15),
        )

        # Backfill Lambda에 필요한 Glue Job 시작 권한 부여
        backfill_lambda.add_to_role_policy(
            iam.PolicyStatement(actions=["glue:StartJobRun"], resources=[glue_job_arn])
        )

    def create_batch_layer(self):
        """
        Layer 04: Batch Layer 생성
        """

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        self.create_feed_layer()
        self.create_batch_layer()
