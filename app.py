#!/usr/bin/env python3
import os
import aws_cdk as cdk
from scripts.load_env import load_environmental_vars
from src.cicd.pipeline_manager import StageManagerWeb, StageManagerMT
from src.core.models.repository import Repository

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

repositories = {
    "dev-website-repo": Repository(
        name="PAP-ui",
        owner="CaerusLabs",
        repo_name="PAP-ui",
        branch="main",
        deployable=True,
        stageType=StageManagerWeb,
        code_star_connection_arn="arn:aws:codestar-connections:us-east-2:260374441616:connection/b31b9d20-3949-4c6a-b379-df087079cba6"  #aws codestar-connections list-connections
    ),
    "dev-api-repo": Repository(
        name="PAP-middle-tier",
        owner="CaerusLabs",
        repo_name="PAP-middle-tier",
        branch="main",
        deployable=False,
        stageType=StageManagerMT,
        code_star_connection_arn="arn:aws:codestar-connections:us-east-2:260374441616:connection/b31b9d20-3949-4c6a-b379-df087079cba6"
    )
}

devWebStack = WebsiteStack(app, "DevWebsiteStack", updateRefererSecret=False, env=env)
dev_site_s3_bucket = devWebStack.website_bucket
cdk.Tags.of(devWebStack).add("AppManagerCFNStackKey", "DevelopmentWebApp")

cicdStack = CICDStack(app, "CiCdPipeline", repositories=repositories, website_bucket=dev_site_s3_bucket, env=env)
cdk.Tags.of(cicdStack).add("AppManagerCFNStackKey", "CiCdPipeline")

vpcStack = VPCStack(app, "VPCCDKStack", env=env)
cdk.Tags.of(vpcStack).add("AppManagerCFNStackKey", "DevelopmentVPC")

cdk.Tags.of(app).add("Project", "RentalPropertiesAgent")

app.synth()