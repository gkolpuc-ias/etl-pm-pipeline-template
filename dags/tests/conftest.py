import pytest
import requests


@pytest.fixture
def mock_requests(monkeypatch):
    class MockInstanceIdentityDocumentResponse:
        def json(self):
            return {
                'region': 'us-east-1',
                'accountId': '000000000000'
            }

    real_requests_get = requests.get

    def mock_requests_get(url):
        if url == 'http://169.254.169.254/latest/dynamic/instance-identity/document':
            return MockInstanceIdentityDocumentResponse()
        return real_requests_get(url)

    monkeypatch.setattr(requests, 'get', mock_requests_get)


@pytest.fixture
def env_config():
    return {
        'env_id': 'test',
        'region': 'us-east-1',
        'deployment_version': '0.0.0',
        'airflow_cluster_id': 'ariflow.test.cluster',
        'assets_location': 'assets_location_path',
        'airflow_aws_conn_id': 'aws_connection_id',
        'pipelines': {
            'test_pipeline': {
              'dag': {
                'schedule': '* * * * *',
                'start_date': '2022-01-01',
                'catchup': False,
                'max_active_runs': 1,
                'use_cloudformation_stack': True
              }
            }
        },
        'aws_resources': {
            'test_app-test-scoring': {
            },
            'test_app-test-prereqs': {
            }
        }
    }
