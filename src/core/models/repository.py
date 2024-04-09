from pydantic import BaseModel
from typing import Type
from src.cicd.pipeline_manager import AbstractStageManager
from aws_cdk.aws_codepipeline import Artifact

class Repository(BaseModel):
    name: str
    owner: str
    repo_name: str
    branch: str
    deployable: bool
    stageType: Type[AbstractStageManager]
    source_output: Artifact = None
    source_action_name: str = None
    source_stage_name: str = None
    build_project_name: str = None
    
    class Config:
        arbitrary_types_allowed = True