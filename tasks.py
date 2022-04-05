"""Project tasks.
See https://www.pyinvoke.org/ for details.
"""
import os

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


@task
def init(ctx):
    # use lower case and '-' as separator
    config = {
        'DAG_NAME': 'grzegorz-daily',
        'PARTNER_NAME': 'grzegorz',
        'SERVICE_NAME': 'daily-processor',
    }

    def ignore_path(path):
        ignore_dirs = ['venv', '.git', '.idea', 'README.md', 'pycache']
        for ignore in ignore_dirs:
            if ignore in path:
                return True
        return False

    from re import sub

    def camel_case(s):
        s = sub(r"(_|-)+", " ", s).title().replace(" ", "")
        return ''.join([s[0].upper(), s[1:]])

    def apply_config(config: dict, additional_config: dict, string: str):
        rename = False
        final_name = string
        for key in additional_config:
            if key in string:
                final_name = final_name.replace(key, additional_config[key])
                rename = True

        for key in config:
            if key in string:
                final_name = final_name.replace(key, config[key])
                rename = True

        if rename:
            return final_name
        else:
            return None

    additional_config = {}
    for key in config:
        additional_config[f'{key}_CAMEL_CASE'] = camel_case(config[key])
        additional_config[f'{key}_UNDERSCORED'] = config[key].replace('-', '_')

    print(config)
    print(additional_config)

    dir_to_template = 'services'
    for r, d, f in os.walk(dir_to_template):
        for file in f:
            src = os.path.join(r, file)
            if not ignore_path(f'{src}'):
                print(f'Changing {src} ...')
                new_name = apply_config(config, additional_config, f'{file}')
                if new_name:
                    dst = os.path.join(r, new_name)
                    os.rename(src, dst)

    for r, d, f in os.walk(dir_to_template, topdown=False):
        # print(f'{r}, {d}, {f}')
        for folder in d:
            src = os.path.join(r, folder)
            print(f'Checking dir {src} ...')
            if not ignore_path(f'{src}'):
                print(f'Renaming dir {src} ...')
                new_name = apply_config(config, additional_config, f'{folder}')
                if new_name:
                    dst = os.path.join(r, new_name)
                    if os.path.exists(dst) and os.path.isdir(dst):
                        import shutil
                        shutil.rmtree(dst)
                    os.rename(src, dst)

    for r, d, f in os.walk(dir_to_template):
        for file in f:
            file_name = os.path.join(r, file)
            if not ignore_path(f'{file_name}'):
                print(f'Changing {file_name} ...')
                fin = open(file_name, "rt")
                data = fin.read()
                new_data = apply_config(config, additional_config, data)
                fin.close()
                if new_data:
                    fin = open(file_name, "wt")
                    fin.write(new_data)
                    fin.close()
