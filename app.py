"""AWS CDK application.
See https://docs.aws.amazon.com/cdk/ for details.
"""

from ias_aws_cdk.pmi import PMIApp

from stacks.PARTNER_NAME_prerequisites_stack import PARTNER_NAMEPrerequisitesStack

# create CDK application
from stacks.PARTNER_NAME_constants import StackName

app = PMIApp(app_name='etl-pm-pipeline-PARTNER_NAME', team_tag='walledgardensplatform',
             repository_tag='etl-pm-pipeline-PARTNER_NAME')

# add shared prerequisites stack
prereqs_stack = PARTNER_NAMEPrerequisitesStack(app, app, StackName.PREREQS)
app.synth()
