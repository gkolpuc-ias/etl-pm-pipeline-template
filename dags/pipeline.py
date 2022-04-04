"""Airflow pipeline DAGs.

See https://airflow.apache.org/docs/stable/ for details.

"""

# keywords to make Airflow pick up DAGs in this file: airflow DAG
import json

import pkg_resources

from etl_pm_pipeline_PARTNER_NAME.dags import DAG_NAME_CAMEL_CASEDag

APP_NAME = 'etl-pm-pipeline-PARTNER_NAME'

# load environment configuration
env_config = json.loads(pkg_resources.resource_string(
    __name__, 'env-config.json'
))

# create DAGs
DAG_NAME_UNDERSCORED_dag = DAG_NAME_CAMEL_CASEDag(APP_NAME, env_config)
