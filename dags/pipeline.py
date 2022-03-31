"""Airflow pipeline DAGs.

See https://airflow.apache.org/docs/stable/ for details.

"""

# keywords to make Airflow pick up DAGs in this file: airflow DAG
import json

import pkg_resources

from etl_pm_pipeline_PARTNER_NAME.dags.metadata_extractor_dag import VendorExtractorDag
from etl_pm_pipeline_PARTNER_NAME.common.score_merger_conf import MtrScoreMergerConfiguration, \
    ImpressionsScoreMergerConfiguration
from etl_pm_pipeline_PARTNER_NAME.dags import (
    SadIpLoaderDag,
    DataLinkFullDownloadDag,
    DataLinkIncrementalDownloadDag,
    BrandSafetyMartingDag,
    ViewabilityMartingDag,
    MetadataExtractorDag,
    VideoContentFetcherDag,
    ScoringDag,
    DiscrepancyCheckerDag,
    QueryVideoIdDag
)

APP_NAME = 'etl-pm-pipeline-youtube'

# load environment configuration
env_config = json.loads(pkg_resources.resource_string(
    __name__, 'env-config.json'
))

# create DAGs
sad_ip_loader_dag = SadIpLoaderDag(APP_NAME, env_config)
download_full_adh_dag = DataLinkFullDownloadDag(APP_NAME, env_config)
query_video_id_dag = QueryVideoIdDag(APP_NAME, env_config)
download_incremental_adh_dag = DataLinkIncrementalDownloadDag(
    APP_NAME, env_config)
brand_safety_marting_dag = BrandSafetyMartingDag(APP_NAME, env_config)
viewability_dag = ViewabilityMartingDag(APP_NAME, env_config)
metadata_extractor_dag = MetadataExtractorDag(APP_NAME, env_config)
vendor_extractor_dag = VendorExtractorDag(APP_NAME, env_config)
scoring_mtr_dag = ScoringDag(
    APP_NAME, MtrScoreMergerConfiguration(env_config, APP_NAME), env_config)
scoring_impressions_dag = ScoringDag(
    APP_NAME, ImpressionsScoreMergerConfiguration(env_config, APP_NAME), env_config)
discrepancy_checker_dag = DiscrepancyCheckerDag(APP_NAME, env_config)
video_content_fetcher_dag = VideoContentFetcherDag(APP_NAME, 'impressions', env_config)
video_content_fetcher_dag_fp = VideoContentFetcherDag(APP_NAME, 'impressionsfp', env_config)
video_content_fetcher_dag_mtr = VideoContentFetcherDag(APP_NAME, 'mtr', env_config)
video_content_fetcher_dag_mtrfp = VideoContentFetcherDag(APP_NAME, 'mtrfp', env_config)
