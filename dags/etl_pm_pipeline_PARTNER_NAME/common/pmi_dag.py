"""Base PMI DAG module."""

from typing import Any, Callable, Mapping
from abc import ABC
from datetime import datetime

import logging
import requests
from dateutil import parser, tz

from airflow.models.dagrun import DagRun
from airflow import settings
from airflow.models import DAG, TaskInstance, BaseOperator
from airflow.contrib.operators.sns_publish_operator import SnsPublishOperator


def _failure_callback(context: Mapping[str, Any]):
    """Callback for when a task fails."""

    dag: PMIDAG = context['dag']
    task_instance: TaskInstance = context['ti']

    return SnsPublishOperator(
        task_id='task_failure_callback',
        aws_conn_id=dag.aws_conn_id,
        target_arn=':'.join([
            "arn:aws:sns",
            dag.aws_env['region'],
            dag.aws_env['accountId'],
            dag.aws_resource_shared('AlarmsTopicName'),
        ]),
        subject='PMI DAG run failure',
        message=(
            f"Airflow task failure:\n"
            f"\n"
            f"\nDAG:             {task_instance.dag_id}"
            f"\nTask:            {task_instance.task_id}"
            f"\nExecution Date:  {task_instance.execution_date}"
            f"\nHost:            {task_instance.hostname}"
            f"\nError:           {context['exception']}"
        )
    ).execute(context)


def _data_date_tz_offset_filter(data_date: str) -> int:
    """Jinja2 filter implementation for getting timezone offset in seconds for the given data date."""

    return round(PMIDAG.DATA_DATE_TZ.utcoffset(datetime(
        *(int(p) for p in data_date.split('-'))
    )).total_seconds())


# pylint: disable=too-many-public-methods
# pylint: disable=too-many-instance-attributes
class PMIDAG(ABC, DAG):
    """Abstract PMI DAG.

    Parameters
    ----------
    pipeline_name
        Name of the pipeline represented by the DAG.
    description
        DAG description.
    app_name
        Project's AWS app (stack) name.
    env_config
        Deployment environment configuration. At the minimum, the following
        properties must be provided:

        * `env_id` - Deployment environment id ("dev", "staging", "prod", etc.).
        * `deployment_version` - DAG deployment version (e.g. "1.2.3").
        * `airflow_cluster_id` - Airflow cluster id.
        * `airflow_aws_conn_id` - Airflow AWS connection id (e.g. "aws_default").
    """

    PRODUCT_DOMAIN = 'etl'

    PRODUCT_NAME = 'pm'

    TEAM = 'weedwackers'

    DATA_DATE_TZ = tz.gettz('America/New_York')

    DATE_PARAMETER_FORMAT = '%Y-%m-%dT%H:%M:%S'

    @staticmethod
    def get_xcom_param(param_name, task: BaseOperator) -> str:
        """Returns a string formatted to pull a parameter from the 'set_parameters' xcom."""
        return f'{{{{ task_instance.xcom_pull(task_ids="{task.task_id}", key="{param_name}") }}}}'

    @staticmethod
    def get_dag(**kwargs) -> 'PMIDAG':
        """Get the DAG (either from the provided arguments or the context)."""
        return kwargs.get('dag', settings.CONTEXT_MANAGER_DAG)

    @staticmethod
    def set_force_parameter(dag_run: DagRun, task_instance: TaskInstance, **kwargs):
        # pylint: disable=unused-argument
        """Sets force parameter if it is provided. Default is False."""
        force_param = dag_run.conf.get('force', False) if dag_run.conf else False
        logging.info('Force parameter is set to %s', force_param)

        force_argument = '--force' if force_param is True else '--no-force'
        logging.info('Setting force: %s', force_argument)
        task_instance.xcom_push(key='force', value=force_argument)

    @staticmethod
    def set_param(
            dag_run: DagRun,
            task_instance: TaskInstance,
            key: str,
            value: Any,
            user_param_handler: Callable = None,
    ) -> Any:
        """Set param in airflow context. Overridden if user provide param in the trigger."""
        param_val = dag_run.conf.get(key) if dag_run.conf else None
        if param_val is not None:
            actual_value = user_param_handler(param_val) if user_param_handler else param_val
            logging.info('User provided %s: %s - parameter will be overridden', key, actual_value)
        else:
            actual_value = value
            logging.info('Setting parameter %s: %s', key, actual_value)

        task_instance.xcom_push(key=key, value=actual_value)
        return actual_value

    def set_date_param(
            self,
            dag_run: DagRun,
            task_instance: TaskInstance,
            **kwargs,
    ):
        # pylint: disable=unused-argument

        # get the date provided from airflow ui or take execution date as default
        default_date = (
            dag_run.conf.get("date", dag_run.execution_date.strftime("%Y%m%d"))
            if dag_run.conf
            else dag_run.execution_date.strftime("%Y%m%d")
        )
        self.set_param(dag_run, task_instance, "default_date", default_date)

    @staticmethod
    def format_input_date_parameter(
            date_str: str,
            output_date_format: str = DATE_PARAMETER_FORMAT
    ) -> str:
        """Converts a valid input date string to the specified output string.

        Typically used for parsing user-provided dates for manual DAG runs.
        """
        return parser.parse(date_str).strftime(output_date_format)

    def __init__(
            self,
            pipeline_name: str,
            *,
            description: str,
            app_name: str,
            env_config: Mapping[str, Any],
    ):
        ABC.__init__(self)

        self._pipeline_name = pipeline_name
        self._partner = 'youtube'
        self._app_name = app_name
        self._env_config = env_config
        self._pipeline_config = env_config['pipelines'][pipeline_name]
        env_id = env_config['env_id']

        # get AWS environment configuration from the Airflow instance
        if '_aws_env' in env_config:  # local deployment
            self._aws_env = env_config['_aws_env']
        else:
            self._aws_env = requests.get(
                'http://169.254.169.254/latest/dynamic/instance-identity/document'
            ).json()

        self._region_designator = ''.join(part[0] for part in self._aws_env['region'].split('-'))

        self._assets_location = env_config['assets_location']

        # AWS Cloudformation stacks
        self._aws_stack_shared = f'etl-pm-shared-{env_id}'
        self._aws_stack_prereqs = f'{app_name}-{env_id}-prereqs'

        self._aws_stack_main = None
        if self._pipeline_config['dag']['use_cloudformation_stack'] is True:
            # Main stack is optional, not all pipelines need dedicated AWS resources.
            self._aws_stack_main = f'{app_name}-{env_id}-{pipeline_name}'

        # default operator arguments
        default_args = {
            'owner': PMIDAG.TEAM,
            'queue': f"{env_config['airflow_cluster_id']}.{env_id}",
            'depends_on_past': False,
            'retries': 0,
            'email_on_failure': False,
            'email_on_retry': False,
        }

        # initialize the DAG
        schedule = self._pipeline_config['dag']['schedule']
        start_date = datetime.strptime(self._pipeline_config['dag']['start_date'], '%Y-%m-%d')
        catchup = self._pipeline_config['dag']['catchup']
        max_active_runs = self._pipeline_config['dag']['max_active_runs']
        deployment_version_major = env_config['deployment_version'].split('.')[0]

        dag_id = '-'.join([
            PMIDAG.PRODUCT_DOMAIN,
            PMIDAG.PRODUCT_NAME,
            self.partner,
            self.pipeline_name,
            f'v{deployment_version_major}',
            env_id,
        ])

        DAG.__init__(
            self,
            dag_id=dag_id,
            description=description,
            default_args=default_args,
            schedule_interval=schedule,
            start_date=start_date,
            catchup=catchup,
            max_active_runs=max_active_runs,
            concurrency=(max_active_runs * 10),
            on_failure_callback=_failure_callback,
            user_defined_filters={
                'data_date_tz_offset': _data_date_tz_offset_filter
            },
            tags=['youtube']
        )

    def aws_resource_shared(self, resource_name: str) -> str:
        """Retrieves an AWS resource from the shared stack."""
        return self._aws_resource(self.aws_stack_shared, resource_name)

    def aws_resource_prereqs(self, resource_name: str) -> str:
        """Retrieves an AWS resource from the prerequisites stack."""
        return self._aws_resource(self.aws_stack_prereqs, resource_name)

    def aws_resource_main(self, resource_name: str) -> str:
        """Retrieves an AWS resource from the main stack."""
        return self._aws_resource(self.aws_stack_main, resource_name)

    def _aws_resource(self, stack_name: str, resource_name: str) -> str:
        """Retrieves an AWS resource from deployment environment configuration."""
        return self.env_config['aws_resources'][stack_name][resource_name]

    @property
    def pipeline_name(self) -> str:
        """Pipeline name."""
        return self._pipeline_name

    @property
    def app_name(self) -> str:
        """Project's AWS app (stack) name."""
        return self._app_name

    @property
    def partner(self) -> str:
        """Name of the partner."""
        return self._partner

    @property
    def env_config(self) -> Mapping[str, Any]:
        """Deployment environment configuration."""
        return self._env_config

    @property
    def pipeline_config(self) -> Mapping[str, Any]:
        """Pipeline environment configuration."""
        return self._pipeline_config

    @property
    def env_id(self) -> str:
        """Deployment environment id (shortcut for `env_config['env_id']`)."""
        return self._env_config['env_id']

    @property
    def region_designator(self) -> str:
        """Short deployment region designator ("ue1", "uw2", etc.)."""
        return self._region_designator

    @property
    def aws_conn_id(self) -> str:
        """Airflow AWS connection id (shortcut for `env_config['airflow_aws_conn_id']`)."""
        return self._env_config['airflow_aws_conn_id']

    @property
    def aws_env(self) -> Mapping[str, Any]:
        """AWS environment information.

        See https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/instance-identity-documents.html for details.

        """
        return self._aws_env

    @property
    def assets_location(self) -> str:
        """DAG assets location (an S3 URL)."""
        return self._assets_location

    @property
    def aws_stack_shared(self) -> str:
        """Name of the shared AWS Cloudformation stack."""
        return self._aws_stack_shared

    @property
    def aws_stack_prereqs(self) -> str:
        """Name of the prerequisites AWS Cloudformation stack."""
        return self._aws_stack_prereqs

    @property
    def aws_stack_main(self) -> str:
        """Name of the main AWS Cloudformation stack."""
        return self._aws_stack_main
