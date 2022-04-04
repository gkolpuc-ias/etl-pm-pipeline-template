import logging
from datetime import datetime, timedelta

from typing import Mapping, Any, Optional
import boto3
from airflow.exceptions import AirflowSkipException
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from dateutil import tz
from dateutil.parser import isoparse

from ...common.config_provider import ConfigProvider
from ...common.utils.jira import create_jira_issue  # pylint: disable=no-name-in-module


class CampaignsExceedingMtrJiraOperator(BaseOperator):

    JIRA_ISSUE_KEY_XCOM = 'jira_issue'
    MAX_ATTACHMENT_SIZE_BYTES = 10 * 1024 * 1024
    PRESIGNED_URL_EXPIRATION_TIME_SEC = 21 * 24 * 60 * 60

    template_fields = ('_exceeding_campaings_no', '_attachment_path')

    @apply_defaults
    def __init__(self,
                 exceeding_campaings_no: str,
                 ticket_config: Optional[Mapping[str, Any]],
                 attachment_bucket: str,
                 attachment_path: str,
                 *args,
                 **kwargs):
        super().__init__(*args, **kwargs)
        self._exceeding_campaings_no = exceeding_campaings_no
        self._ticket_config = ticket_config
        self._region_name = ConfigProvider().env_config['region']
        self._attachment_bucket = attachment_bucket
        self._attachment_path = attachment_path

    def execute(self, context):
        if int(self._exceeding_campaings_no) == 0:
            raise AirflowSkipException('No campaigns exceeding mtr')

        if not self._ticket_config:
            raise AirflowSkipException('Skipping jira integration')

        ref_date = isoparse(context['ts'])

        logging.info("Creating jira ticket with attachment s3://%s/%s", self._attachment_bucket, self._attachment_path)
        jira, issue = create_jira_issue(self._region_name, self._ticket_config, ref_date)

        logging.info("Create issue with key %s", issue.key)
        self.xcom_push(context, key=self.JIRA_ISSUE_KEY_XCOM, value=issue.key)

        self._add_attachment(jira, issue, ref_date)

    def _add_attachment(self, jira, issue, ref_date: datetime):
        s3_client = boto3.client("s3")
        s3_object = s3_client.get_object(Bucket=self._attachment_bucket, Key=self._attachment_path)
        self.logger.info('Attachemnt size %s bytes', s3_object.content_length)

        if s3_object.content_length <= self.MAX_ATTACHMENT_SIZE_BYTES:
            attachment_name = ref_date.strftime('campaigns_exceeding_mtr_for_%Y%m%d.csv')
            jira.add_attachment(issue, s3_object["Body"].read(), attachment_name)
        else:
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self._attachment_bucket, 'Key': self._attachment_path},
                ExpiresIn=self.PRESIGNED_URL_EXPIRATION_TIME_SEC)
            valid_until = datetime.now(tz=tz.UTC) + timedelta(seconds=self.PRESIGNED_URL_EXPIRATION_TIME_SEC)
            jira.add_comment(issue, f'Report available via: {url}'
                                    f'\nLink valid to: {valid_until.strftime("%Y-%m-%d %H:%M")}')
