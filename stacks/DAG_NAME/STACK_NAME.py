"""Data loader launcher stack"""
from aws_cdk import (
    aws_iam as iam,
    aws_s3 as s3,
    core,
)
from ias_aws_cdk.pmi import PMIApp, get_region_designator

from etl_pm_pipeline_cdk_common.ecs_base_stack import EcsStack
from ..PARTNER_NAME_prerequisites_stack import PARTNER_NAMEPrerequisitesStack


class STACK_NAME_Stack(EcsStack):
    def __init__(
            self,
            scope: core.Construct,
            app: PMIApp,
            stack_id: str,
            *,
            prereqs_stack: PARTNER_NAMEPrerequisitesStack,
    ):
        super().__init__(
            scope,
            app,
            stack_id,
            prereqs_stack=prereqs_stack,
            name="DAG_NAME stack",
            ecs_task_exec_role_description="ecs task execution role"
        )
        region_designator = get_region_designator(self.region)




