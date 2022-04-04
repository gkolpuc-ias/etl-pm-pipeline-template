"""Data loader support module."""

import json
import os

from airflow import AirflowException
from airflow.contrib.operators.sns_publish_operator import SnsPublishOperator
from airflow.utils.decorators import apply_defaults

from ..pmi_dag import PMIDAG


class DataLoaderTriggerOperator(SnsPublishOperator):
    """Data loader trigger operator."""

    @apply_defaults
    def __init__(
            self,
            data_url: str,
            *args,
            **kwargs
    ):
        dag = PMIDAG.get_dag()

        if not (data_url.startswith('gcs://') or data_url.startswith('s3://')):
            raise AirflowException(f'Unsupported protocol: {data_url}')

        self.data_url = data_url

        super().__init__(
            aws_conn_id=dag.aws_conn_id,
            target_arn=dag.env_config['data_load_trigger_sns_topic_arn'],
            message=json.dumps({
                'client_id': dag.app_name,
                'data_url': data_url
            }),
            *args, **kwargs
        )

    @staticmethod
    def from_s3(bucket: str, path: str, *args, **kwargs) -> 'DataLoaderTriggerOperator':
        data_url = os.path.join("s3://", bucket, path)
        return DataLoaderTriggerOperator(data_url=data_url, *args, **kwargs)

    @staticmethod
    def from_gcs(bucket: str, path: str, *args, **kwargs) -> 'DataLoaderTriggerOperator':
        data_url = os.path.join("gcs://", bucket, path)
        return DataLoaderTriggerOperator(data_url=data_url, *args, **kwargs)
