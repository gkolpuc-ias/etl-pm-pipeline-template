from argparse import Namespace

from etl_pm_pipeline_common.aws.emr.pmi_spark_job import PMISparkJob  # pylint: disable=import-error
from pyspark.sql import DataFrame, SparkSession


def execute(spark: SparkSession, args: Namespace) -> None:
    # TODO
    # spark code here...
    print('Not implemented yet...')


class PipelineSparkJob(PMISparkJob):

    def __init__(self):
        super().__init__()

        self.add_argument('--input-path', required=True)
        self.add_argument('--output-path', required=True)

    def _get_job_name(self, _):
        return "Facebook raw data conversion"

    def execute(self, spark: SparkSession, args: Namespace):
        execute(spark, args)


if __name__ == '__main__':
    PipelineSparkJob().run()
