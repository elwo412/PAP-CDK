from lib.core.WebsiteManager import WebsiteManagerAbstract
from aws_cdk import (
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_route53 as route53,
    aws_certificatemanager as acm,
    aws_cloudfront_origins as origins,
    RemovalPolicy,
    aws_cognito as cognito,
    aws_iam as iam,
    Stack
)
from constructs import Construct
import secrets

class WebsiteManager(WebsiteManagerAbstract):
    def __init__(self, scope):
        super().__init__(scope)
        self.secret_referer_value = secrets.token_hex(16)
    
    def setup_s3(self):
        self.bucket = s3.Bucket(self.scope, "DevWebsiteBucket",
            website_index_document="index.html",
            public_read_access=False,  # Block public access
            removal_policy=RemovalPolicy.DESTROY,
        )
        self.setup_s3_policy()
        
    def setup_s3_policy(self):
        self.bucket.add_to_resource_policy(iam.PolicyStatement(
            sid="DenyAccessWithoutReferer",
            effect=iam.Effect.DENY,
            principals=[iam.StarPrincipal()],
            actions=["s3:GetObject"],
            resources=[f"{self.bucket.bucket_arn}/*"],
            conditions={"StringNotEquals": {"aws:Referer": self.secret_referer_value}}
        ))
        self.bucket.add_to_resource_policy(iam.PolicyStatement(
            sid="AllowAccessWithReferer",
            effect=iam.Effect.ALLOW,
            principals=[iam.StarPrincipal()],
            actions=["s3:GetObject"],
            resources=[f"{self.bucket.bucket_arn}/*"],
            conditions={"StringEquals": {"aws:Referer": self.secret_referer_value}}
        ))

    def setup_cloudfront(self):
        oai = cloudfront.OriginAccessIdentity(self.scope, "OAI")

        # Grant read access to the OAI on the S3 bucket
        self.bucket.grant_read(oai)

        # Create a CloudFront distribution with the OAI
        self.distribution = cloudfront.Distribution(self.scope, "DevDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(self.bucket, origin_access_identity=oai, custom_headers={"Referer": self.secret_referer_value}),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
        )

        # Update the S3 bucket policy to restrict access to the CloudFront OAI
        self.bucket.add_to_resource_policy(iam.PolicyStatement(
            actions=["s3:GetObject"],
            resources=[self.bucket.arn_for_objects("*")],
            principals=[iam.ArnPrincipal(oai._arn())],
            effect=iam.Effect.ALLOW
        ))

    def setup_authentication(self):
        # Create the Cognito user pool with email and username sign-in options
        self.user_pool = cognito.UserPool(self.scope, "DevUserPool",
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

    def setup_route53(self):
        # Setup Route 53 if required for the development stack
        pass
    
    @property
    def website_bucket(self) -> s3.Bucket:
        return self.bucket