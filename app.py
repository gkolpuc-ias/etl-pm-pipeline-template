"""AWS CDK application.
See https://docs.aws.amazon.com/cdk/ for details.
"""

from ias_aws_cdk.pmi import PMIApp

from stacks.DAG_NAME_UNDERSCORED import DAG_NAME_CAMEL_CASEStack
from stacks.PARTNER_NAME_prerequisites_stack import PARTNER_NAME_CAMEL_CASEPrerequisitesStack

# create CDK application
from stacks.PARTNER_NAME_constants import PARTNER_NAME_CAMEL_CASEConstants

app = PMIApp(app_name='etl-pm-pipeline-PARTNER_NAME', team_tag='walledgardensplatform',
             repository_tag='etl-pm-pipeline-PARTNER_NAME')

# add shared prerequisites stack
prereqs_stack = PARTNER_NAME_CAMEL_CASEPrerequisitesStack(app, app, PARTNER_NAME_CAMEL_CASEConstants.PREREQS)
DAG_NAME_UNDERSCORED_stack = DAG_NAME_CAMEL_CASEStack(
    app, app, PARTNER_NAME_CAMEL_CASEConstants.DAG_NAME_UNDERSCORED, prereqs_stack=prereqs_stack
)
app.synth()
