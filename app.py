#!/usr/bin/env python3
import os

import aws_cdk as cdk

from rental_properties_agent_cdk.CICD.CICDStack import CICDStack, CICDStack_v2
from lib.VPC.VPCStack import VPCStack
from lib.WEB.WebsiteStack import WebsiteStack


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

devwebstack = WebsiteStack(app, "DevWebsiteStack")
dev_site_s3_bucket = devwebstack.website_bucket
CICDStack_v2(app, "CiCdPipeline", repositories=repositories, website_bucket=dev_site_s3_bucket)
VPCStack(app, "VPCCDKStack")

app.synth()
