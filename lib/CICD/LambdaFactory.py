from lib.core.LambdaFactory import AbstractLambdaFactory
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
from constructs import Construct

class CICDLambdaFactory(AbstractLambdaFactory):
    def __init__(self, scope: Construct):
        super().__init__(scope)
        
    def create_github_status_lambda(self, scope, codepipeline_arn: str, artifact_bucket: s3.Bucket):
        source_dir = "lib/CICD/Assets/lambda/github_status"
        self.create_package_directory(source_dir)
        github_status_lambda: lambda_.Function = self.create_lambda(
            id="GithubStatusNotifier",
            handler="github_status.handler",
            runtime=lambda_.Runtime.PYTHON_3_8,
            code=lambda_.Code.from_asset(source_dir+"/package"),
            environment={
                'GITHUB_REPO_OWNER': 'CaerusLabs',
            },
            timeout=Duration.seconds(15),
            )

        # Add the necessary permission to the Lambda function's execution role
        github_status_lambda.role.add_to_policy(iam.PolicyStatement(
            actions=["codepipeline:GetPipelineState"],
            resources=[codepipeline_arn]
        ))
        
        github_status_lambda.role.add_to_policy(iam.PolicyStatement(
            actions=["secretsmanager:GetSecretValue"],
            resources=["arn:aws:secretsmanager:us-east-2:260374441616:secret:github/build_status/PAP-YcYH8O"]
        ))
        
        # Grant read access to the artifact bucket
        artifact_bucket.grant_read(github_status_lambda)

        # Explicitly set the dependency on the S3 bucket
        github_status_lambda.node.add_dependency(artifact_bucket)

        return github_status_lambda

    def create_discord_notifier_lambda(self, scope, codepipeline_arn):
        source_dir = "lib/CICD/Assets/lambda/discord_notifier"
        self.create_package_directory(source_dir)
        discord_notifier : lambda_.Function = self.create_lambda(
            id="DiscordNotifier",
            handler="discord_notifier.handler",
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset(source_dir+"/package"),
            environment={
                'GITHUB_REPO_OWNER': 'CaerusLabs',
            },
            timeout=Duration.seconds(15),
            )

        # Add the necessary permission to the Lambda function's execution role
        discord_notifier.role.add_to_policy(iam.PolicyStatement(
            actions=["codepipeline:GetPipelineState"],
            resources=[codepipeline_arn]
        ))
    
        discord_notifier.role.add_to_policy(iam.PolicyStatement(
            actions=["secretsmanager:GetSecretValue"],
            resources=["arn:aws:secretsmanager:us-east-2:260374441616:secret:github/discord_build_statuses/PAP-o7uQEZ"]
        ))

        return discord_notifier