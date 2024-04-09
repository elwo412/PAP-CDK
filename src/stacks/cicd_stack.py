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

from src.cicd.pipeline_manager import PipelineManager, StageManagerWeb
from src.cicd.lambda_factory import LambdaFactory
from src.cicd.notification_manager import NotificationManager
from src.core.models.repository import Repository

class CICDStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, repositories: dict, website_bucket: s3.Bucket, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        dev_web_repo_info: Repository = repositories.get("dev-website-repo")
        artifact_bucket_web = s3.Bucket(self, "ArtifactBucket", removal_policy=RemovalPolicy.DESTROY)
        pipeline_manager_web = PipelineManager(self, dev_web_repo_info.stageType, artifact_bucket_web, pipeline_name="RentalPropertiesAgentCICDPipeline", repository_info=dev_web_repo_info, website_bucket=website_bucket)
        pipeline_manager_web.configure_pipeline()

        lambda_factory = LambdaFactory(self)
        github_lambda = lambda_factory.create_github_status_lambda(self, [pipeline_manager_web.pipeline.pipeline_arn], [artifact_bucket_web])
        discord_lambda = lambda_factory.create_discord_notifier_lambda(self, [pipeline_manager_web.pipeline.pipeline_arn])
        
        dev_web_repo_info.pipeline_name = pipeline_manager_web.pipeline.pipeline_name

        notification_manager = NotificationManager(self)
        notification_manager.create_build_start_rule(dev_web_repo_info, github_lambda)
        notification_manager.create_build_success_rule(dev_web_repo_info, github_lambda, discord_lambda)
        notification_manager.create_build_failure_rule(dev_web_repo_info, github_lambda, discord_lambda)