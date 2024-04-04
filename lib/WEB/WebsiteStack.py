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
from lib.WEB.WebsiteManager import WebsiteManager

class WebsiteStack(Stack):
    def __init__(self, scope: Construct, id: str, updateRefererSecret: bool = True, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        self.website_manager = WebsiteManager(self, updateReferer=updateRefererSecret)

        self.website_manager.setup_s3()
        self.website_manager.setup_cloudfront()
        self.website_manager.setup_authentication()
        # self.setup_route53()  # Uncomment if Route 53 is needed for the development environment

    @property
    def website_bucket(self) -> s3.Bucket:
        return self.website_manager.bucket