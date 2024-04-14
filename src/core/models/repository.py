from pydantic import BaseModel
from typing import Type, Optional, List, Any
from src.cicd.pipeline_manager import AbstractStageManager
from aws_cdk.aws_codepipeline import Artifact

class Repository(BaseModel):
    name: str
    owner: str
    repo_name: str
    branch: str
    deployable: bool
    stageType: Type[AbstractStageManager]
    code_star_connection_arn: str
    source_output: Artifact = None
    source_action_name: str = None
    source_stage_name: str = None
    build_project_name: str = None
    pipeline_name: str = None
    build_dependencies: List[Any] = []
    
    class Config:
        arbitrary_types_allowed = True
        
    def has_build_dependency_of_type(self, dependency_type: Type) -> bool:
        return any(isinstance(dependency, dependency_type) for dependency in self.build_dependencies)
    
    def get_build_dependency_of_type(self, dependency_type: Type) -> Optional[Any]:
        for dependency in self.build_dependencies:
            if isinstance(dependency, dependency_type):
                return dependency

        return None