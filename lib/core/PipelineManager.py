from abc import ABC, abstractmethod
from aws_cdk import (
    aws_codepipeline as codepipeline,
)
from aws_cdk.aws_s3 import Bucket
from constructs import Construct

class AbstractPipelineManager(ABC):
    def __init__(self, scope: Construct, artifact_bucket: Bucket, pipeline_name: str):
        self.scope = scope
        self.artifact_bucket = artifact_bucket
        self.pipeline_name = pipeline_name
        self.stage_manager: AbstractStageManager = None
        self._pipeline: codepipeline.Pipeline = None

    def create_pipeline(self):
        self._pipeline = codepipeline.Pipeline(
            self.scope, "Pipeline",
            artifact_bucket=self.artifact_bucket,
            pipeline_name=self.pipeline_name
        )

    @abstractmethod
    def configure_pipeline(self):
        pass
    
class AbstractStageManager(ABC):
    def __init__(self, pipeline: codepipeline.Pipeline, scope: Construct):
        self._pipeline = pipeline
        self._scope = scope

    @abstractmethod
    def add_source_stage(self, repo):
        pass

    @abstractmethod
    def add_build_stage(self, repo):
        pass

    @abstractmethod
    def add_manual_approval_stage(self):
        pass
    
    def add_deploy_stage(self, repo, website_bucket):
        raise NotImplementedError