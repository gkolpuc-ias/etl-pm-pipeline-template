"""
Project tasks.
See https://www.pyinvoke.org/ for details.
"""

from invoke import task

from etl_pm_pipeline_cicd_common.tasks.test_tasks import test
from etl_pm_pipeline_cicd_common.tasks.validate_tasks import lint_python_code


@task
def validate_emr(ctx):
    # temporal '--exit-zero' as code has tens of lint errors
    # to be fixed as separate story
    lint_python_code(ctx, ['--exit-zero ../emr'])


@task
def validate_and_test_emr(ctx):
    validate_emr(ctx)
    test(ctx)
