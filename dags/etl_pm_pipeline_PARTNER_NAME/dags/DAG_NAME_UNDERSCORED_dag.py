from datetime import datetime, timedelta
from typing import Any, Mapping

from airflow.utils.helpers import chain
from airflow.operators.python_operator import PythonOperator
from airflow.models.taskinstance import TaskInstance
from airflow.models.dagrun import DagRun
from etl_pm_pipeline_airflow_common.pmi_dag import PMIDAG

from ..common.config_provider import ConfigProvider

# from ..common.operators import (
#     PmiEcsFargateOperator,
#     get_ecs_container_override,
# )

PIPELINE_NAME = "DAG_NAME"

TASK_TIMEOUT = timedelta(hours=1)


class DAG_NAME_CAMEL_CASEDag(PMIDAG):

    def set_parameters(
            self,
            dag_run: DagRun,
            execution_date: datetime,
            task_instance: TaskInstance,
            **kwargs,
    ):
        """Sets all accepted input parameters"""

        default_end_date = execution_date
        default_start_date = default_end_date - timedelta(hours=24)
        self.set_param(
            dag_run,
            task_instance,
            'start_date',
            default_start_date.strftime(PMIDAG.DATE_PARAMETER_FORMAT),
            user_param_handler=self.format_input_date_parameter,
        )
        self.set_param(
            dag_run,
            task_instance,
            'end_date',
            default_end_date.strftime(PMIDAG.DATE_PARAMETER_FORMAT),
            user_param_handler=self.format_input_date_parameter,
        )

    def __init__(
            self,
            app_name: str,
            env_config: Mapping[str, Any],
    ):
        super().__init__(
            PIPELINE_NAME,
            description=f"PARTNER_NAME - DAG_NAME ",
            app_name=app_name,
            env_config=env_config,
        )
        with self:
            config = ConfigProvider()

            set_parameters_task = PythonOperator(
                task_id='set_parameters',
                provide_context=True,
                python_callable=self.set_parameters,
                op_kwargs={'lookback_hours': 24}
            )

            # task = PmiEcsFargateOperator(
            #     task_id=f"SERVICE_NAME_UNDERSCORED_task",
            #     task_definition=config.get_DAG_NAME_UNDERSCORED("SERVICE_NAME_CAMEL_CASEDefinitionArn"),
            #     security_group_id=config.get_DAG_NAME_UNDERSCORED("SecurityGroupId"),
            #     execution_timeout=TASK_TIMEOUT,
            #     container_overrides=[
            #         get_ecs_container_override(
            #             "SERVICE_NAME_UNDERSCORED",
            #             [
            #                 "SERVICE_NAME_UNDERSCORED.py",
            #                 "--date", "{{ ds }}",
            #             ]
            #         ),
            #     ],
            #     log_group_name=config.get_DAG_NAME_UNDERSCORED("LogGroupName"),
            #     log_stream_prefix="ecs/SERVICE_NAME_UNDERSCORED",
            # )
            #
            chain(
                set_parameters_task
                # , task
            )
