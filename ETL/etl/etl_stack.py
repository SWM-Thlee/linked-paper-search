from aws_cdk import Aws, Duration, Fn, RemovalPolicy, Size, Stack
from aws_cdk import aws_batch as batch
from aws_cdk import aws_ec2 as ec2
from aws_cdk import aws_ecr_assets
from aws_cdk import aws_ecs as ecs
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_glue as glue
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_opensearchservice as opensearch
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_s3_notifications as s3n
from aws_cdk import aws_secretsmanager as secretsmanager
from constructs import Construct

# Layer 01: Glue Job
GLUE_BUCKET_NAME = "etl-glue-script"
PAPER_FEED_BUCKET_NAME = "paper-feed"


# Layer 04: Batch Layer
DOMAIN_NAME = "opensearch-document-store"
DOMAIN_DATA_NODE_INSTANCE_TYPE = (
    "r7g.xlarge.search"  # vCPU: 2 memory: 32GB Bill/Hour: USD 0.429
)
DOMAIN_DATA_NODE_INSTANCE_COUNT = (
    3  # 현재 데이터 노드 하나만 사용 후 추후 scale-out 필요 시 증가
)
DOMAIN_INSTANCE_VOLUME_SIZE = 200  # 100만개 논문 수집 시 약 26GB 저장 공간 필요
DOMAIN_AZ_COUNT = 1  # Multi-AZ 설정
DOMAIN_MASTER_NODE_INSTANCE_TYPE = "c7g.large.search"
DOMAIN_MASTER_NODE_INSTANCE_COUNT = 3

## To enable UW, please make master node count as 3 or 5, and UW node count as minimum 2
## Also change data node to be non T2/T3 as UW does not support T2/T3 as data nodes
DOMAIN_UW_NODE_INSTANCE_TYPE = "ultrawarm1.medium.search"
DOMAIN_UW_NODE_INSTANCE_COUNT = 0
BATCH_ECS_DOCKER_DIR = "batch_ecs"


class EtlStack(Stack):

    def create_feed_layer(self):
        """
        Layer 01: Glue Job 생성
        """

        glue_bucket = s3.Bucket.from_bucket_name(
            self, "GlueScriptsBucket", bucket_name=GLUE_BUCKET_NAME
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

        self.paper_feed_bucket.grant_put(glue_role)  # 업로드 권한 부여

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
                "METADATA_BUCKET": PAPER_FEED_BUCKET_NAME,
            },
            timeout=Duration.minutes(5),
        )
        # Lambda가 paper-feed 버킷을 읽을 수 있도록 권한 부여
        self.paper_feed_bucket.grant_read(trigger_lambda.role)

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
                "METADATA_BUCKET": PAPER_FEED_BUCKET_NAME,
            },
            timeout=Duration.minutes(15),
        )

        # Backfill Lambda에 필요한 Glue Job 시작 권한 부여
        backfill_lambda.add_to_role_policy(
            iam.PolicyStatement(actions=["glue:StartJobRun"], resources=[glue_job_arn])
        )

    def create_batch_producer_layer(self):
        """
        Layer 03: Batch Job Producer 생성
        s3 버킷에 추가된 논문들을 batch job 제출
        """

        # Lambda 함수 생성
        lambda_submit_batch_job = _lambda.Function(
            self,
            "SubmitBatchJob",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="trigger_03_batch_job.handler",  # Lambda 핸들러
            code=_lambda.Code.from_asset("lambda"),  # Lambda 코드가 저장된 디렉토리
            environment={
                "BATCH_JOB_QUEUE": self.job_queue_arn,
                "BATCH_JOB_DEFINITION": self.job_definition_arn,
            },
            timeout=Duration.minutes(5),
        )

        # S3 객체 생성 이벤트에 대한 Lambda 트리거 추가
        notification = s3n.LambdaDestination(lambda_submit_batch_job)

        # S3 버킷에 이벤트 알림 설정 (객체 생성 시 Lambda 트리거)
        self.paper_feed_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED, notification
        )

        # Lambda에 S3 읽기 권한 부여
        self.paper_feed_bucket.grant_read(lambda_submit_batch_job)

        # Lambda에 Batch 작업 제출 권한 부여
        lambda_submit_batch_job.add_to_role_policy(
            iam.PolicyStatement(
                actions=["batch:SubmitJob"],
                resources=["*"],  # 필요한 경우 더 구체적인 리소스를 설정
            )
        )

    def create_batch_layer(self):
        """
        Layer 04: Batch Layer 생성
        """

        # OpenSearch 마스터 사용자 역할 생성
        opensearch_master_role = iam.Role(
            self,
            "OpenSearchMasterRole",
            assumed_by=iam.ServicePrincipal("opensearchservice.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonOpenSearchServiceFullAccess"
                ),
            ],
        )

        # ECS Task Role 생성
        ecs_task_role = iam.Role(
            self,
            "DocumentEmbedderTaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
        )

        # S3 read 권한 추가
        ecs_task_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3ReadOnlyAccess")
        )
        # OpenSearch에 대한 권한 추가
        ecs_task_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonOpenSearchServiceFullAccess"
            )
        )

        # CloudWatch Logs 권한 추가
        ecs_task_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "service-role/AmazonECSTaskExecutionRolePolicy"
            )
        )

        # VPC 및 네트워크 리소스에 대한 읽기 권한 추가
        ecs_task_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ReadOnlyAccess")
        )

        # CloudWatch Full Access 권한 추가
        ecs_task_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchFullAccess")
        )

        # OpenSearch용 보안 그룹 생성
        opensearch_sg = ec2.SecurityGroup(
            self,
            "OpenSearchSecurityGroup",
            vpc=self.vpc,
            description="Allow all inbound traffic for OpenSearch",
            allow_all_outbound=True,
        )

        # 모든 인바운드 트래픽을 허용
        opensearch_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.all_traffic(),
            description="Allow all inbound traffic",
        )

        # OpenSearch에 접근하기 위한 Search Service Task Role ARN 가져오기
        search_service_task_role_arn = Fn.import_value("SearchServiceTaskRoleArn")

        # OpenSearch 도메인 생성
        opensearch_domain = opensearch.Domain(
            self,
            "DocumentStoreOpenSearch",
            domain_name=DOMAIN_NAME,
            version=opensearch.EngineVersion.OPENSEARCH_2_15,
            vpc=self.vpc,
            vpc_subnets=self.vpc_subnets,
            security_groups=[
                opensearch_sg
            ],  # OpenSearch 기본 보안 그룹은 inbound 트래픽을 허용하지 않음
            capacity=opensearch.CapacityConfig(
                multi_az_with_standby_enabled=False,
                data_node_instance_type=DOMAIN_DATA_NODE_INSTANCE_TYPE,
                data_nodes=DOMAIN_DATA_NODE_INSTANCE_COUNT,
                master_node_instance_type=DOMAIN_MASTER_NODE_INSTANCE_TYPE,
                master_nodes=DOMAIN_MASTER_NODE_INSTANCE_COUNT,
                warm_instance_type=DOMAIN_UW_NODE_INSTANCE_TYPE,
                warm_nodes=DOMAIN_UW_NODE_INSTANCE_COUNT,
            ),
            ebs=opensearch.EbsOptions(
                enabled=True,
                volume_size=DOMAIN_INSTANCE_VOLUME_SIZE,
                volume_type=ec2.EbsDeviceVolumeType.GP3,
            ),
            removal_policy=RemovalPolicy.DESTROY,
            enforce_https=True,
            node_to_node_encryption=True,
            encryption_at_rest=opensearch.EncryptionAtRestOptions(enabled=True),
            # zone_awareness=opensearch.ZoneAwarenessConfig(  # Multi-AZ 설정 data node 2개 이상일 때만 사용 가능
            #     enabled=True,
            #     availability_zone_count=DOMAIN_AZ_COUNT,
            # ),
            fine_grained_access_control=opensearch.AdvancedSecurityOptions(
                master_user_arn=opensearch_master_role.role_arn
            ),
            access_policies=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    principals=[
                        iam.ArnPrincipal(ecs_task_role.role_arn),
                        iam.ArnPrincipal(search_service_task_role_arn),
                    ],  # ecs_task_role에게만 접근 권한 부여
                    actions=["es:*"],
                    resources=[
                        f"arn:aws:es:{self.region}:{self.account}:domain/opensearch-document-store/*"
                    ],
                )
            ],
        )

        # Docker 이미지 빌드 및 ECR에 업로드
        docker_image_asset = aws_ecr_assets.DockerImageAsset(
            self,
            "ecr-docker-image-asset",
            platform=aws_ecr_assets.Platform.LINUX_AMD64,
            directory=BATCH_ECS_DOCKER_DIR,  # Dockerfile이 있는 경로 (batch_ecs/Dockerfile)
        )

        # docker_image_asset.repository.add_lifecycle_rule(tag_prefix_list=["latest"])

        docker_container_image = ecs.ContainerImage.from_docker_image_asset(
            docker_image_asset
        )

        # AWS Batch Job Definition 생성 (Fargate 사용)
        job_definition = batch.EcsJobDefinition(
            self,
            "DocumentEmbedderBatchJobDefinition",
            retry_attempts=10,
            container=batch.EcsFargateContainerDefinition(
                self,
                "DocumentEmbedderFargateContainer",
                image=docker_container_image,
                cpu=4,
                memory=Size.mebibytes(4096 * 2),  # 2GB 설정 시 out of memory 발생
                execution_role=ecs_task_role,
                job_role=ecs_task_role,
            ),
        )

        # AWS Batch Fargate 기반의 Compute Environment 생성
        compute_environment = batch.FargateComputeEnvironment(
            self,
            "DocumentEmbedderComputeEnvironment",
            vpc=self.vpc,
            vpc_subnets=self.vpc_subnets[0],
            maxv_cpus=16,
            replace_compute_environment=True,  # 기존 Compute Environment 대체
        )

        # AWS Batch Job Queue 생성
        job_queue = batch.JobQueue(
            self,
            "DocumentEmbedderJobQueue",
            compute_environments=[
                batch.OrderedComputeEnvironment(
                    compute_environment=compute_environment,
                    order=1,
                )
            ],
        )

        # VPC 엔드포인트 추가
        # 중요! 해당 endpoint 없이 ecr에 접근하면 NAT Gateway를 통해 인터넷을 통해 접근해야 함
        self.vpc.add_interface_endpoint(
            "EcrApiEndpoint", service=ec2.InterfaceVpcEndpointAwsService.ECR
        )

        self.vpc.add_interface_endpoint(
            "EcrDkrEndpoint", service=ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER
        )

        # S3 VPC 엔드포인트도 필요한 경우 추가
        self.vpc.add_gateway_endpoint(
            "S3Endpoint", service=ec2.GatewayVpcEndpointAwsService.S3
        )

        self.job_queue_arn = job_queue.job_queue_arn
        self.job_definition_arn = job_definition.job_definition_arn

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        # 기존 Web Infra VPC lookup
        self.vpc = ec2.Vpc.from_lookup(
            self, "ExistingVpc", vpc_id="vpc-058b5208a767d5d1c"
        )
        # private subnet 선택
        self.vpc_subnets = [
            ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                availability_zones=[self.vpc.availability_zones[0]],
            ),
        ]

        # S3 버킷 참조
        self.paper_feed_bucket = s3.Bucket.from_bucket_name(
            self, "PaperFeedBucket", bucket_name=PAPER_FEED_BUCKET_NAME
        )

        self.create_feed_layer()
        self.create_batch_layer()
        self.create_batch_producer_layer()
