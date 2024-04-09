from abc import ABC, abstractmethod
from constructs import Construct

class WebsiteManagerAbstract(ABC):
    def __init__(self, scope: Construct):
        self.scope = scope

    @abstractmethod
    def setup_s3(self):
        """
        Setup S3 bucket for website content.
        """
        pass

    @abstractmethod
    def setup_cloudfront(self):
        """
        Setup CloudFront distribution for the website.
        """
        pass

    @abstractmethod
    def setup_authentication(self):
        """
        Setup authentication mechanism (e.g., Cognito for user authentication).
        """
        pass

    @abstractmethod
    def setup_route53(self):
        """
        Setup Route 53 for domain management.
        """
        pass