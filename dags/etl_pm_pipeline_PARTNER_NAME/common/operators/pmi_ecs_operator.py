"""Custom ECS operator module."""

from typing import Dict, List

from airflow.contrib.operators.ecs_operator import ECSOperator
from airflow.utils.decorators import apply_defaults

from ..pmi_dag import PMIDAG


def get_ecs_container_override(container_name: str, command_list: List[str]) -> Dict:
    """Returns a dictionary with the proper formatting for ECS container overrides.

    Parameters
    ----------
    container_name
        Name of the Docker container defined in the task definition.
    command_list
        List of runtime commands to pass the Docker container.

    Returns
    -------
    Dict
        Dictionary with the correct keys needed for the ECSOperator.

    """
    return {
        'name': container_name,
        'command': command_list,
    }


class PmiEcsFargateOperator(ECSOperator):
    """ECS operator customized for PMI Fargate workloads.

    Parameters
    ----------
    task_definition
        Name of the ECS Fargate task definition to run.
    security_group_id
        EC2 security group ID used to run the task in.
    container_overrides
        List of dictionaries with commands to pass to task container(s).
        Use the `get_ecs_container_override()` helper method.
    log_group_name
        Optional name of a CloudWatch log group. If provided, logs from this group
        will be available in the Airflow UI after the task executes.
    log_stream_prefix
        Optional name of a CloudWatch log stream prefix. Should be provided if
        `log_group_name` is provided.
    args, kwargs
        Standard Airflow operator arguments.

    """

    @apply_defaults
    def __init__(
            self,
            *args,
            task_definition: str,
            security_group_id: str,
            container_overrides: List[Dict],
            log_group_name: str = None,
            log_stream_prefix: str = None,
            **kwargs,
    ):
        dag = PMIDAG.get_dag(**kwargs)

        ecs_cluster_name = dag.aws_resource_prereqs('ECSClusterName')
        network_configuration = {
            'awsvpcConfiguration': {
                'securityGroups': [security_group_id],
                'subnets': dag.aws_resource_prereqs('VPCPrivateSubnetIds').split(','),
            },
        }
        tags = {
            'team': PMIDAG.TEAM,
            'project': dag.pipeline_name,
            'repository': dag.app_name,
        }

        super().__init__(
            task_definition=task_definition,
            cluster=ecs_cluster_name,
            aws_conn_id=dag.aws_conn_id,
            launch_type='FARGATE',
            network_configuration=network_configuration,
            overrides={
                'containerOverrides': container_overrides,
            },
            tags=tags,
            awslogs_group=log_group_name,
            awslogs_stream_prefix=log_stream_prefix,
            *args,
            **kwargs,
        )
