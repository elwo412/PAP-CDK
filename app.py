#!/usr/bin/env python3
import os
import aws_cdk as cdk
from scripts.load_env import load_environmental_vars
from src.cicd.pipeline_manager import StageManagerWeb, StageManagerMT
from src.core.models.repository import Repository

from src.stacks.cicd_stack import CICDStack
from src.stacks.vpc_stack import VPCStack
from src.stacks.website_stack import WebsiteStack
from src.stacks.middle_tier_stack import MiddleTierStack

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
        deployable=True,
        stageType=StageManagerMT,
        code_star_connection_arn="arn:aws:codestar-connections:us-east-2:260374441616:connection/b31b9d20-3949-4c6a-b379-df087079cba6"
    )
}

vpcStack = VPCStack(app, "VPCCDKStack", env=env)
private_lambda_instance = vpcStack.private_lambda_instance
cdk.Tags.of(vpcStack).add("AppManagerCFNStackKey", "DevelopmentVPC")

devWebStack = WebsiteStack(app, "DevWebsiteStack", updateRefererSecret=False, env=env)
dev_site_s3_bucket = devWebStack.website_bucket
repositories["dev-website-repo"].build_dependencies = [dev_site_s3_bucket]
cdk.Tags.of(devWebStack).add("AppManagerCFNStackKey", "DevelopmentWebApp")

devMiddleTierStack = MiddleTierStack(app, "DevMiddleTierStack", private_lambda=private_lambda_instance, env=env)
dev_lambda_function = devMiddleTierStack.lambda_function
repositories["dev-api-repo"].build_dependencies = [dev_lambda_function]
cdk.Tags.of(devMiddleTierStack).add("AppManagerCFNStackKey", "DevelopmentMiddleTier")

cicdStack = CICDStack(app, "CiCdPipeline", repositories=repositories, env=env)
cdk.Tags.of(cicdStack).add("AppManagerCFNStackKey", "CiCdPipeline")

cdk.Tags.of(app).add("Project", "RentalPropertiesAgent")

app.synth()