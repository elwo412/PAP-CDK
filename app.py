#!/usr/bin/env python3
import os
import aws_cdk as cdk
from scripts.load_env import load_environmental_vars

from src.stacks.cicd_stack import CICDStack
from src.stacks.vpc_stack import VPCStack
from src.stacks.website_stack import WebsiteStack

# Load environment-specific variables
load_environmental_vars()

# Fetch account and region from environment variables
account = os.environ.get('AWS_ACCOUNT_ID')
region = os.environ.get('AWS_REGION')

app = cdk.App()
# RentalPropertiesAgentCdkStack(app, "RentalPropertiesAgentCdkStack",
#     # If you don't specify 'env', this stack will be environment-agnostic.
#     # Account/Region-dependent features and context lookups will not work,
#     # but a single synthesized template can be deployed anywhere.

#     # Uncomment the next line to specialize this stack for the AWS Account
#     # and Region that are implied by the current CLI configuration.

#     #env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),

#     # Uncomment the next line if you know exactly what Account and Region you
#     # want to deploy the stack to. */

#     #env=cdk.Environment(account='123456789012', region='us-east-1'),

#     # For more information, see https://docs.aws.amazon.com/cdk/latest/guide/environments.html
#     )

repositories = [
    {"name": "PAP-ui", "owner": "CaerusLabs", "repo_name": "PAP-ui", "branch": "main", "type": "frontend"},
]

devwebstack = WebsiteStack(app, "DevWebsiteStack", updateRefererSecret=True, env={'account': account, 'region': region})
dev_site_s3_bucket = devwebstack.website_bucket
CICDStack(app, "CiCdPipeline", repositories=repositories, website_bucket=dev_site_s3_bucket, env={'account': account, 'region': region})
VPCStack(app, "VPCCDKStack", env={'account': account, 'region': region})

app.synth()
