"""Prerequisites stack module."""

from aws_cdk import (
    aws_sns as sns,
    aws_s3 as s3,
    aws_dynamodb as dynamodb,
    core
)

from ias_aws_cdk.pmi import PMIApp
from etl_pm_pipeline_cdk_common.constants import SHARED_RESOURCES_STACK_NAME_BASE
from etl_pm_pipeline_cdk_common.base_prerequisites_stack import BasePrerequisitesStack


class PARTNER_NAME_CAMEL_CASEPrerequisitesStack(BasePrerequisitesStack):
    """YouTube Prerequisites stack."""

    def __init__(self, scope: core.Construct, app: PMIApp, cid: str):
        super().__init__(
            scope=scope,
            app=app,
            cid=cid,
            description="PM pipeline PARTNER_NAME: prerequisite resources."
        )

        self.app = app

        # S3 resources
        self.raw_bucket = s3.Bucket.from_bucket_name(
            self,
            "DataLakeRawBucket",
            core.Fn.import_value(
                f"{SHARED_RESOURCES_STACK_NAME_BASE}-{app.env_id}:DataLakeRawBucketName"
            ),
        )
        self.discrepancy_bucket = s3.Bucket.from_bucket_name(
            self,
            "DataLakeDiscrepancyBucket",
            core.Fn.import_value(
                f"{SHARED_RESOURCES_STACK_NAME_BASE}-{app.env_id}:DataLakeDiscrepancyBucketName"
            ),
        )
        self.logging_bucket = s3.Bucket.from_bucket_name(
            self,
            f"iaspl-pipeline-logging-{self.region_designator}-de-{app.env_id}",
            f"iaspl-pipeline-logging-{self.region_designator}-de-{app.env_id}",
        )
        self.transfer_bucket = s3.Bucket.from_bucket_name(
            self,
            f"ias-transfer-{app.env_id}",
            f"ias-transfer-{app.env_id}",
        )
        self.processed_bucket = s3.Bucket.from_bucket_name(
            self,
            "DataLakeProcessedBucket",
            core.Fn.import_value(
                f"{SHARED_RESOURCES_STACK_NAME_BASE}-{app.env_id}:PipelineProcessedBucketName"
            ),
        )

        # EMR role and granting access to S3 resources
        self.add_glue_access_to_emr(self.emr_job_role)
        self.add_read_access_to_emr(self.emr_job_role)
        self.add_athena_access_to_emr(self.emr_job_role)
        self.raw_bucket.grant_read_write(self.emr_job_role)
        self.discrepancy_bucket.grant_read_write(self.emr_job_role)
        self.logging_bucket.grant_put(self.emr_job_role, objects_key_pattern="emr_logs/*")

        # SNS resources
        self.alarms_topic = self.alarms_topic()
        self.notifications_topic = self.notifications_topic()

        # Dynamodb resources

        # Table to track execution processes, triggering DAGs, save states, etc.
        # set up to replace HDFS flag files used in etl-pm-youtube-adh
        self._status_table = dynamodb.Table(
            self,
            "StatusTable",
            table_name=f"{app.safe_app_name}-status-table",
            partition_key=dynamodb.Attribute(
                name="id", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=core.RemovalPolicy.DESTROY,
        )

        core.CfnOutput(
            self,
            "StatusTableName",
            value=self._status_table.table_name,
            description="Name of the DynamoDB table to track execution processes, triggering DAGs, save states, etc.",
        )

        core.CfnOutput(
            self,
            "S3TransferBucket",
            value=self.transfer_bucket.bucket_name,
            description="Name of the transfer bucket",
        )

    def alarms_topic(self):
        alarms_topic = sns.Topic.from_topic_arn(
            self,
            "AlarmsTopic",
            core.Fn.import_value(
                f"{SHARED_RESOURCES_STACK_NAME_BASE}-{self.app.env_id}:AlarmsTopicArn"
            )
        )
        alarms_topic.grant_publish(self.emr_job_role)
        return alarms_topic

    def notifications_topic(self):
        notifications_topic = sns.Topic.from_topic_arn(
            self,
            "NotificationsTopic",
            core.Fn.import_value(
                f"{SHARED_RESOURCES_STACK_NAME_BASE}-{self.app.env_id}:NotificationsTopicArn"
            )
        )
        notifications_topic.grant_publish(self.emr_job_role)
        return notifications_topic

    def status_table(self) -> dynamodb.Table:
        """Dynamodb status table"""
        return self._status_table
