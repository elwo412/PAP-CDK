from lib.core.WebsiteManager import WebsiteManagerAbstract
from aws_cdk import (
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_route53 as route53,
    aws_certificatemanager as acm,
    aws_cloudfront_origins as origins,
    RemovalPolicy,
    aws_cognito as cognito,
    Stack
)
from constructs import Construct

class WebsiteManager(WebsiteManagerAbstract):
    def __init__(self, scope):
        super().__init__(scope)
    
    def setup_s3(self):
        self.bucket = s3.Bucket(self.scope, "DevWebsiteBucket",
            website_index_document="index.html",
            public_read_access=False, # Block public access
            removal_policy=RemovalPolicy.DESTROY,
        )

    def setup_cloudfront(self):
        oai = cloudfront.OriginAccessIdentity(self.scope, "OAI")
        self.bucket.grant_read(oai)

        self.distribution = cloudfront.Distribution(self.scope, "DevDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(self.bucket, origin_access_identity=oai),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
            ),
        )

    def setup_authentication(self):
        self.user_pool = cognito.UserPool(self.scope, "UserPool",
            self_sign_up_enabled=True,
            sign_in_aliases=cognito.SignInAliases(email=True),
        )

    def setup_route53(self):
        # Setup Route 53 if required for the development stack
        pass
    
    @property
    def website_bucket(self) -> s3.Bucket:
        return self.bucket