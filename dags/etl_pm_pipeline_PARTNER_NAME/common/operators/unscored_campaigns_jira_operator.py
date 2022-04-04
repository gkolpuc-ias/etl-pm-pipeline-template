import logging

from typing import Optional, Any, Mapping
import snowflake.connector
from airflow import AirflowException
from airflow.exceptions import AirflowSkipException
from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults
from dateutil.parser import isoparse

from ..config_provider import ConfigProvider
from ..utils.jira import create_jira_issue
from ..utils.snowflake import get_snowflake_credentials


class BsUnscoredCampaingsJiraOperator(BaseOperator):
    JIRA_ISSUE_KEY_XCOM = 'jira_issue'
    UNSCORED_RATE_THRESHOLD = 6.0
    QUERY_TEMPLATE = '''
    SELECT 
        SUM(imps) AS TOTAL_IMPRESSIONS, 
        SUM(CASE WHEN ADT_RATING_ID = 0 AND VIO_RATING_ID = 0 AND ALC_RATING_ID = 0 AND DRG_RATING_ID = 0 
        AND OFF_RATING_ID = 0 AND HAT_RATING_ID = 0 THEN imps ELSE 0 END) AS UNSCORED_IMPRESSIONS
    FROM 
        {brandsafety_table}
    WHERE 
        measurement_source_id IN (2, 3, 7, 12, 13, 14, 15) 
        AND hit_date = '{hit_date}'
    '''

    template_fields = ('_brandsafety_table_name',)

    @apply_defaults
    def __init__(self,
                 ticket_config: Mapping[str, Any],
                 *args,
                 brandsafety_table_name: str = 'AGG_PARTNER_MEASURED_BRANDSAFETY',
                 unscored_threshold_rate: float = UNSCORED_RATE_THRESHOLD,
                 **kwargs):
        super().__init__(*args, **kwargs)
        config = ConfigProvider()
        self._ticket_config = ticket_config
        self._unscored_threshold_rate = unscored_threshold_rate
        self._brandsafety_table_name = brandsafety_table_name
        self._sf_conf = config.env_config['snowflake']
        self._region_name = config.env_config['region']

    def execute(self, context):
        if not self._ticket_config:
            raise AirflowSkipException('No jira ticket configured')

        rate = self._get_unscored_rate(context['ds'])
        if not rate:
            raise AirflowException('Can not calculate scored rate')

        if rate > self._unscored_threshold_rate:
            ref_date = isoparse(context['ts'])
            _, issue = create_jira_issue(self._region_name, self._ticket_config, ref_date)

            logging.info("Create issue with key %s", issue.key)
            self.xcom_push(context, key=self.JIRA_ISSUE_KEY_XCOM, value=issue.key)

    def _get_unscored_rate(self, hit_date: str) -> Optional[float]:
        sql = self.QUERY_TEMPLATE.format(hit_date=hit_date, brandsafety_table=self._brandsafety_table_name)
        logging.info('Executing query %s', sql)
        conn = snowflake.connector.connect(**get_snowflake_credentials(self._sf_conf, self._region_name))
        cursor = conn.cursor()
        try:
            cursor.execute(sql)
            row = cursor.fetchone()
            if row and row[1]:
                return float(row[1]) / float(row[0]) * 100.0
            return None
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
