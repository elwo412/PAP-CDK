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
    aws_cognito as cognito,
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
            proxy=False
        )
        
        # temporary endpoint
        self.rest_api.root.add_method("GET")
        
        self.setup_cognito_user_pool()
        
    def setup_cognito_user_pool(self):
        # Create the Cognito user pool with email and username sign-in options
        self.user_pool = cognito.UserPool(self, "DevUserPool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(
                email=True,
                username=True  # Allows sign in with a username
            ),
            user_pool_name='DevelopersUserPool',  # Optional: give a name to the user pool
            auto_verify=cognito.AutoVerifiedAttrs(email=True)  # Automatically verify email addresses
        )

        # Create an app client with a hosted UI
        self.user_pool_client = self.user_pool.add_client("AppClient",
            auth_flows=cognito.AuthFlow(
                user_password=True,  # Enables username and password-based authentication
                user_srp=True  # Enables Secure Remote Password (SRP) protocol
            ),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(
                    authorization_code_grant=True,  # Enable the authorization code grant flow
                    implicit_code_grant=True  # Enable the implicit code grant flow
                ),
                callback_urls=["https://www.example.com/callback"],  # Add your callback URL(s)
                logout_urls=["https://www.example.com/logout"]  # Add your sign-out URL(s)
            ),
            generate_secret=False  # Set to true if the app client requires a secret
        )

        # Set up the hosted UI domain
        self.user_pool.add_domain("HostedUIDomain",
            cognito_domain=cognito.CognitoDomainOptions(
                domain_prefix="devuserspoolio"  # Choose a unique domain prefix
            )
        )
        
    @property
    def lambda_function(self) -> lambda_.Function:
        return self._lambda_function
    
    @property
    def cognito_user_pool(self) -> cognito.UserPool:
        return self.user_pool
    
    @property
    def api_gateway(self) -> apigateway.RestApi:
        return self.rest_api