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

env = cdk.Environment(account=account, region=region)

app = cdk.App()

repositories = [
    {"name": "PAP-ui", "owner": "CaerusLabs", "repo_name": "PAP-ui", "branch": "main", "type": "frontend"},
]

devwebstack = WebsiteStack(app, "DevWebsiteStack", updateRefererSecret=False, env=env)
dev_site_s3_bucket = devwebstack.website_bucket
CICDStack(app, "CiCdPipeline", repositories=repositories, website_bucket=dev_site_s3_bucket, env=env)
VPCStack(app, "VPCCDKStack", env=env)

app.synth()