""" 
CI CD Stack
-------------
This stack is responsible for creating the CI/CD pipeline. It uses the AWS CodePipeline construct to create
a pipeline that listens for changes in the GitHub repository and triggers the build and deploy stages.
"""

from constructs import Construct
import os, shutil, sys
from aws_cdk import (
    Stack,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_s3 as s3,
    aws_lambda as lambda_,
    aws_codebuild as codebuild,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_logs,
    SecretValue,
    RemovalPolicy,
    Duration
)

from src.cicd.pipeline_manager import PipelineManager
from src.cicd.lambda_factory import LambdaFactory
from src.cicd.notification_manager import NotificationManager

class CICDStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, repositories: list, website_bucket: s3.Bucket, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        artifact_bucket = s3.Bucket(self, "ArtifactBucket", removal_policy=RemovalPolicy.DESTROY)
        pipeline_manager = PipelineManager(self, artifact_bucket, pipeline_name="RentalPropertiesAgentCICDPipeline", repositories=repositories, website_bucket=website_bucket)
        pipeline_manager.configure_pipeline()

        lambda_factory = LambdaFactory(self)
        github_lambda = lambda_factory.create_github_status_lambda(self, pipeline_manager.pipeline.pipeline_arn, artifact_bucket)
        discord_lambda = lambda_factory.create_discord_notifier_lambda(self, pipeline_manager.pipeline.pipeline_arn)

        notification_manager = NotificationManager(self, pipeline_manager.pipeline.pipeline_name)
        for repo in repositories:
            notification_manager.create_build_start_rule(repo, github_lambda)
            notification_manager.create_build_success_rule(repo, github_lambda, discord_lambda)
            notification_manager.create_build_failure_rule(repo, github_lambda, discord_lambda)