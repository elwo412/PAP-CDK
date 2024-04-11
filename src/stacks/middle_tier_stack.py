"""
Middle tier stack -- responsible for creating the fastapi lambda function and api gateway
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
    aws_apigateway as apigateway,
    aws_logs,
    SecretValue,
    RemovalPolicy,
    Duration
)
class MiddleTierStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, private_lambda: lambda_.Function, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self._lambda_function = private_lambda
        
        # Create the API Gateway REST API
        self.rest_api = apigateway.LambdaRestApi(
            self, "FastApiEndpoint",
            handler=self._lambda_function,
            proxy=True
        )
        
    @property
    def lambda_function(self) -> lambda_.Function:
        return self._lambda_function
    
    @property
    def api_gateway(self) -> apigateway.RestApi:
        return self.rest_api