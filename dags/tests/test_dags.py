# pylint: disable=missing-module-docstring, missing-function-docstring, missing-class-docstring
# pylint: disable=redefined-outer-name, unused-argument

import json
import os
import sys

import pytest
import requests
from airflow import DAG
from airflow.models import DagBag

from ..etl_pm_pipeline_youtube.common import PMIDAG

EXPECTED_NUMBER_OF_DAGS = 15


@pytest.fixture(autouse=True)
def mock_requests(monkeypatch):
    class MockInstanceIdentityDocumentResponse:
        def json(self):
            return {"region": "us-east-1", "accountId": "000000000000"}

    real_requests_get = requests.get

    def mock_requests_get(url):
        if url == "http://169.254.169.254/latest/dynamic/instance-identity/document":
            return MockInstanceIdentityDocumentResponse()
        return real_requests_get(url)

    monkeypatch.setattr(requests, "get", mock_requests_get)


def updated_config(env):
    with open("../envs-config.json", "r") as env_config_file:
        env_config = json.load(env_config_file)[env]

    env_config.update(
        {
            "env_id": "test",
            "deployment_version": "0.0.0",
            "assets_location": "s3://assets-bucket/path/to/assets",
            "aws_resources": {
                "etl-pm-shared-test": {
                    "AlarmsTopicName": "alarms",
                    "AlarmsTopicArn": "sns::alarms",
                    "NotificationsTopicName": "notifications",
                    "NotificationsTopicArn": "sns::notifications",
                    "DataLakeDiscrepancyBucketName": "iasdl-pipeline-discrepancy-ue1-pmi-dev",
                    "DataLakeDiscrepancyBucketDataPrefix": "discrepancy/",
                    "PipelineProcessedBucketName": "iasdl-pipeline-processed-ue1-pmi-dev",
                },
                "etl-pm-pipeline-PARTNER_NAME-test-prereqs": {
                    "VPCPrivateSubnetIds": "subnet-a,subnet-b",
                    "ECSClusterName": "ecs.test.cluster",
                },
                "etl-pm-pipeline-PARTNER_NAME-test-SERVICE_NAME": {
                    "LogGroupName": "log-group",
                    "SecurityGroupId": "security-group",
                }
            },
        }
    )
    return env_config


@pytest.fixture
def env_config():
    """Writes test config to env-config.json file. File is deleted after tests finish."""
    env_config = updated_config("dev")
    with open("env-config.json", "w") as env_config_file:
        json.dump(env_config, env_config_file, indent=2)

    yield env_config
    os.remove("env-config.json")


@pytest.fixture
def env_config_stg():
    """Writes test config to env-config.json file. File is deleted after tests finish."""
    env_config = updated_config("staging")
    with open("env-config.json", "w") as env_config_file:
        json.dump(env_config, env_config_file, indent=2)

    yield env_config
    os.remove("env-config.json")


@pytest.fixture
def env_config_prod():
    """Writes test config to env-config.json file. File is deleted after tests finish."""
    env_config = updated_config("prod")
    with open("env-config.json", "w") as env_config_file:
        json.dump(env_config, env_config_file, indent=2)

    yield env_config
    os.remove("env-config.json")


def load_and_check_dags():
    """Imports all DAGs to validate they compile and have certain default values set."""
    # Adds 'dags' package to path in order for Airflow to import submodules
    import dags     # pylint: disable=import-outside-toplevel

    sys.path.append(os.path.dirname(dags.__file__))

    dag_bag = DagBag(dag_folder="pipeline.py", include_examples=False)
    assert len(dag_bag.dags) == EXPECTED_NUMBER_OF_DAGS
    assert not dag_bag.import_errors

    for _, dag in dag_bag.dags.items():
        assert isinstance(dag, DAG)

        if isinstance(dag, PMIDAG):
            assert dag.env_config["env_id"] == "test"
            assert dag.aws_env["region"] == "us-east-1"
            assert dag.aws_env["accountId"] == "000000000000"


def test_import_dags(env_config):
    load_and_check_dags()


def test_import_dags_stg(env_config_stg):
    load_and_check_dags()


def test_import_dags_prod(env_config_prod):
    load_and_check_dags()
