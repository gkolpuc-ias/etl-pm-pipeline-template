"""Project tasks.
See https://www.pyinvoke.org/ for details.
"""
from etl_pm_pipeline_cicd_common.tasks.airflow_tasks import (
    deploy_dags_to_local_airflow,
    init_local_airflow,
    start_airflow,
    build_airflow_image
)
from etl_pm_pipeline_cicd_common.tasks.deploy_tasks import deploy_to_aws
from etl_pm_pipeline_cicd_common.tasks.validate_tasks import (
    lint_python_code, validate_json_schema,
)

from invoke import task

APP_NAME = 'etl-pm-pipeline-PARTNER_NAME'

AWS_STACKS = {
    'etl-pm-shared-{env_id}',
    'etl-pm-pipeline-PARTNER_NAME-{env_id}-prereqs',
    # ADD NEW CDK STACKS HERE
}


@task
def validate_stacks(ctx):
    lint_python_code(ctx, ['app.py', 'stacks'])


@task
def validate(ctx):
    lint_python_code(ctx, ['tasks.py'])

    validate_json_schema(ctx, 'envs-config.json', 'envs-config.schema.json')


@task(help={
    'env-id': "Deployment environment id (dev, staging, prod, etc.).",
    'env-config-json': "Optional environment configuration JSON string for non-standard environments."
})
def deploy(ctx, env_id, env_config_json=None):
    deploy_to_aws(ctx, env_id, app_name=APP_NAME, aws_stacks=AWS_STACKS, env_config_json=env_config_json)


@task
def deploy_locally(ctx):
    deploy_dags_to_local_airflow(ctx=ctx, app_name=APP_NAME, aws_stacks=AWS_STACKS)


@task
def init_airflow(ctx):
    init_local_airflow(
        ctx,
        app_name=APP_NAME,
        short_name='PARTNER_NAME',
        airflow_cluster_name='airflow.aws.pmi.common.common.dev'
    )


@task
def build_image(ctx):
    build_airflow_image(ctx=ctx, app_name=APP_NAME)


@task
def airflow(ctx, init=False):
    if init:
        init_airflow(ctx)
    build_image(ctx)
    deploy_locally(ctx)
    start_airflow(ctx)
