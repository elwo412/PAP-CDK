from src.core.abstracts.website_manager import WebsiteManagerAbstract
from aws_cdk import (
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_route53 as route53,
    aws_certificatemanager as acm,
    aws_cloudfront_origins as origins,
    RemovalPolicy,
    aws_cognito as cognito,
    aws_iam as iam,
    Stack,
    Duration
)
from constructs import Construct
import secrets, os, json
from src.core.secrets_manager import SecretManager

class WebsiteManager(WebsiteManagerAbstract):
    def __init__(self, scope, updateReferer):
        super().__init__(scope)
        sm = SecretManager()
        if updateReferer:
            sm.update_secret("REFERER_SECRET", secrets.token_urlsafe(32))
        
        self.secret_referer_value = sm.get_secret("REFERER_SECRET")
    
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
        
        # Define a cache policy for development
        cache_policy = cloudfront.CachePolicy(self.scope, "DevCachePolicy",
            max_ttl=Duration.minutes(10),
            default_ttl=Duration.minutes(5),
            min_ttl=Duration.seconds(0),
            comment="Cache policy for development environment"
        )

        # Create a CloudFront distribution with the OAI
        self.distribution = cloudfront.Distribution(self.scope, "DevDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(self.bucket, origin_access_identity=oai, custom_headers={"Referer": self.secret_referer_value}),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cache_policy
            ),
        )

        # Update the S3 bucket policy to restrict access to the CloudFront OAI
        self.bucket.add_to_resource_policy(iam.PolicyStatement(
            actions=["s3:GetObject"],
            resources=[self.bucket.arn_for_objects("*")],
            principals=[iam.ArnPrincipal(oai._arn())],
            effect=iam.Effect.ALLOW
        ))

    def setup_route53(self):
        # Setup Route 53 if required for the development stack
        pass
    
    @property
    def website_bucket(self) -> s3.Bucket:
        return self.bucket