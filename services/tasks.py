"""
Project tasks.
See https://www.pyinvoke.org/ for details.
"""

from etl_pm_pipeline_cicd_common.tasks.test_tasks import test_services
from etl_pm_pipeline_cicd_common.tasks.validate_tasks import validate_services

from invoke import task


@task
def validate_and_test_services(ctx):
    validate_services(ctx)
    test_services(ctx)
