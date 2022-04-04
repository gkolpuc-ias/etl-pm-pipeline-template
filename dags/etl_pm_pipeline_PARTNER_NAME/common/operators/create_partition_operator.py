import os

from typing import List, Any, Dict
from airflow.contrib.hooks.aws_hook import AwsHook
from airflow.models import BaseOperator

from .. import PMIDAG
from ..score_merger_conf import GlueTable
from ..utils import split_s3_url


class CreatePartitionOperator(BaseOperator):
    """
    Airflow operator for glue table partition creation based on partition location.
    Operator compares table location with partition location (which have to be match) and extract partition from path.
    Notice that partition directories should be build like partition_name1=value1/partition_name2=value2.
    """

    template_fields = ('partition_location',)

    def __init__(self,
                 *args,
                 table: GlueTable,
                 partition_location: str,
                 **kwargs):
        super().__init__(*args, **kwargs)

        dag = PMIDAG.get_dag()

        self.aws_conn_id = dag.aws_conn_id
        self.partition_location = partition_location
        self.table = table

    def execute(self, context):
        if not self.is_partition_location_exist():
            raise RuntimeError(f'Partition location {self.partition_location} does not exist')

        glue = AwsHook(self.aws_conn_id).get_client_type('glue')

        storage_desc = self._get_storage_descriptor(glue, self.table)
        storage_desc['Location'] = self.partition_location
        self._create_partition(glue, self.table, storage_desc, self.get_values_from_path())

    def get_values_from_path(self) -> List[str]:
        location = self.table.location
        if not location:
            raise RuntimeError(f'Table {self.table.name} location not provided')

        try:
            idx = self.partition_location.index(location)
        except ValueError:
            # pylint: disable=raise-missing-from
            raise RuntimeError(f"Partition location [{self.partition_location}] "
                               f"does not match to table location [{location}]")

        values = []
        for partition in self.partition_location[idx + len(location):].split('/'):
            parts = partition.split('=')
            if len(parts) != 2:
                raise RuntimeError(f"Can't determine partition value based location part {partition}")
            values.append(parts[1])

        if not values:
            raise RuntimeError('Partition values not found')

        return values

    def _get_storage_descriptor(self, glue_client, table: GlueTable) -> Dict[str, Any]:
        self.log.info("getting Glue table information for %s.%s", table.db_name, table.table_name)
        return glue_client.get_table(
            DatabaseName=table.db_name,
            Name=table.table_name
        )['Table']['StorageDescriptor']

    def _create_partition(self, glue_client, table: GlueTable, storage_desc, values: List[Any]) -> None:
        values_str = ', '.join(str(p) for p in values)
        try:
            self.log.info("creating partition for location %s using values %s", storage_desc['Location'], values_str)
            glue_client.create_partition(
                DatabaseName=table.db_name,
                TableName=table.table_name,
                PartitionInput={
                    'StorageDescriptor': storage_desc,
                    'Values': values
                }
            )
        except glue_client.exceptions.AlreadyExistsException:
            self.log.info("Partition exists. Updating partition for location %s using values %s",
                          storage_desc['Location'], values_str)
            glue_client.update_partition(
                DatabaseName=table.db_name,
                TableName=table.table_name,
                PartitionValueList=values,
                PartitionInput={
                    'StorageDescriptor': storage_desc,
                    'Values': values
                }
            )

    def is_partition_location_exist(self) -> bool:
        s3_client = AwsHook(self.aws_conn_id).get_client_type("s3")
        bucket, prefix = split_s3_url(self.partition_location)
        contents = s3_client.list_objects_v2(
            Bucket=bucket,
            Prefix=os.path.join(prefix, ''),
            Delimiter="/",
            MaxKeys=1
        ).get("Contents", [])
        return len(contents) > 0
