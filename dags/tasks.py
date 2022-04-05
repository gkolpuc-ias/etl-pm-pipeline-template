"""
Project tasks.
See https://www.pyinvoke.org/ for details.
"""
from invoke import task

from etl_pm_pipeline_cicd_common.tasks.validate_tasks import lint_python_code
from etl_pm_pipeline_cicd_common.tasks.test_tasks import test


@task
def validate_dags(ctx):
    lint_python_code(ctx, ['etl_pm_pipeline_*'])
    lint_python_code(ctx, ['*.py'])
    lint_python_code(ctx, ['tests'])


@task
def validate_and_test_dags(ctx):
    validate_dags(ctx)
    test(ctx)
