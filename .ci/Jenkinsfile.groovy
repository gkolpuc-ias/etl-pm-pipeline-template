final approverGroup = 'integralads*Walled Gardens Platform'
final chefApiKeyCredsId = 'airflow-chef-client'

Map settings = [
    pipeline_generator: global_pipeline_generator,
    additional_credentials: ['airflow-gd-deploy']
]

// This code runs only on a PR pipeline
pullRequestPipeline {
    registerPrCommentTriggers(['.*deploy to dev.*'])

    onPrComment('.*deploy to dev.*') {
        runToolChainsSh(settings, [
            'invoke -e deploy dev'
        ].join('\n'))
    }
}

// Run unit tests and deploy to dev on PR and Tag builds
pullRequestAndTagPipeline {
    Map testAndValidateTasks = [ failFast: false ]

    testAndValidateTasks['Validate'] = {
        stage('Validate') {
            buildAgent(settings) {
                runToolChainsSh(settings, 'invoke -e validate;')
            }
        }
    }

    testAndValidateTasks['Stacks'] = {
        stage('Validate - Stacks') {
            buildAgent(settings) {
                runToolChainsSh(settings, 'invoke -e validate-stacks')
            }
        }
    }

    testAndValidateTasks['Airflow'] = {
        stage('Validate & Test - Airflow') {
            buildAgent(settings) {
                runToolChainsSh(settings, [
                    'cd dags',
                    'virtualenv airflow_venv -p python3.6',
                    'source airflow_venv/bin/activate',
                    'python -m pip install --upgrade pip',
                    'python -m pip install -r requirements_dags.txt --use-deprecated=legacy-resolver',
                    'airflow initdb',
                    'invoke -e validate-and-test-dags',
                ].join('\n'))
            }
        }
    }

    testAndValidateTasks['Services'] = {
        stage('Validate & Test - Services') {
            buildAgent(settings) {
                runToolChainsSh(settings, [
                    'cd services',
                    'virtualenv services_venv -p python3.6',
                    'source services_venv/bin/activate',
                    'python -m pip install --upgrade pip',
                    'python -m pip install -r requirements_services.txt',
                    'invoke -e validate-and-test-services',
                ].join('\n'))
            }
        }
    }

     testAndValidateTasks['EMR'] = {
        stage('Validate & Test - EMR') {
            buildAgent(settings) {
                runToolChainsSh(settings, [
                    'cd emr',
                    'virtualenv emr_venv -p python3.6',
                    'source emr_venv/bin/activate',
                    'python -m pip install --upgrade pip',
                    'python -m pip install -r requirements_emr.txt',
                    'invoke -e validate-and-test-emr',
                ].join('\n'))
            }
        }
    }

    stage('Validate & Test') {
        parallel(testAndValidateTasks)
    }

    deployStage(settings, ias_env: 'dev', approvers: approverGroup) {
        withCredentials([file(credentialsId: chefApiKeyCredsId, variable: 'CHEF_API_KEY')]) {
            runToolChainsSh(settings, 'invoke -e deploy dev')
        }
    }
}

branchPipeline('master') {
    createTagOnMergeTo(version_file: 'version.properties', branch: 'master')
}

tagReleasePipeline {
    deployStage(settings, ias_env: 'staging', approvers: approverGroup) {
        withCredentials([file(credentialsId: chefApiKeyCredsId, variable: 'CHEF_API_KEY')]) {
            runToolChainsSh(settings, 'invoke -e deploy staging')
        }
    }
    deployStage(settings, ias_env: 'prod', approvers: approverGroup) {
        withCredentials([file(credentialsId: chefApiKeyCredsId, variable: 'CHEF_API_KEY')]) {
            runToolChainsSh(settings, 'invoke -e deploy prod')
        }
    }
}
