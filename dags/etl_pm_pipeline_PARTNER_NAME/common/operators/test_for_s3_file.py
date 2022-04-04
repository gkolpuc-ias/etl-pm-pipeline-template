

from airflow.models.baseoperator import BaseOperator
from airflow.operators.python_operator import PythonOperator
from airflow.exceptions import AirflowSkipException
from ..youtube_common import list_s3_files



def _test_s3_file(
        s3_bucket: str,
        s3_prefix: str,
        skip_if_exists: bool,
        task: BaseOperator,
        **kwargs,
):
    # pylint: disable=unused-argument
    log = task.log
    files_in_prefix = len(list_s3_files(s3_bucket, s3_prefix, False))
    log.info(f"files in : {s3_prefix} : {files_in_prefix}")
    if (files_in_prefix > 0) == skip_if_exists:
        raise AirflowSkipException


class TestS3FileOperator(PythonOperator):
    def __init__(
            self,
            *args,
            s3_bucket: str,
            s3_prefix: str,
            skip_if_exists: bool,
            **kwargs,
    ):
        super().__init__(
            python_callable=_test_s3_file,
            provide_context=True,
            op_kwargs={
                "s3_bucket": s3_bucket,
                "s3_prefix": s3_prefix,
                "skip_if_exists": skip_if_exists,
            },
            *args,
            **kwargs,
        )
