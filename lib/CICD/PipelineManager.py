from lib.core.PipelineManager import AbstractPipelineManager, AbstractStageManager
from aws_cdk import (
    Stack,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_s3 as s3,
    aws_lambda as lambda_,
    aws_codebuild as codebuild,
)
from constructs import Construct

class CICDPipelineManager(AbstractPipelineManager):
    def __init__(self, scope, artifact_bucket, pipeline_name, repositories):
        super().__init__(scope, artifact_bucket, pipeline_name)
        self.create_pipeline()
        self.repositories = repositories
        self.stage_manager = CICDStageManager(self._pipeline, scope)
        
    def configure_pipeline(self):
        """
        Configures the pipeline by adding source, manual approval, and build stages for each repository.

        For each repository in the `repositories` list, this method:
        1. Adds a source stage that pulls the latest code from the repository.
        2. Adds a manual approval stage that pauses the pipeline until manual approval is given.
        3. Adds a build stage that builds the code from the repository.
        """
        for repo in self.repositories:
            self.stage_manager.add_source_stage(repo)
            self.stage_manager.add_manual_approval_stage()
            self.stage_manager.add_build_stage(repo)
            
    @property
    def pipeline(self):
        return self._pipeline
            
            
class CICDStageManager(AbstractStageManager):
    def __init__(self, pipeline: codepipeline.Pipeline, scope: Construct):
        super().__init__(pipeline, scope)
    
    def add_source_stage(self, repo: dict):
        CI_action_name = f"{repo['name']}_Source"
        CI_stage_name = f"{repo['name']}_SourceStage"
        source_output = codepipeline.Artifact()
        source_action = codepipeline_actions.CodeStarConnectionsSourceAction(
            action_name=CI_action_name,
            connection_arn="arn:aws:codestar-connections:us-east-2:260374441616:connection/b31b9d20-3949-4c6a-b379-df087079cba6", #aws codestar-connections list-connections
            owner=repo['owner'],
            repo=repo['repo_name'],
            output=source_output,
            branch=repo.get('branch', 'main'),
            variables_namespace=f"{repo['name']}_SourceVariables"
        )
        self._pipeline.add_stage(stage_name=CI_stage_name, actions=[source_action])
        repo.update({
            "source_output": source_output,
            "source_action_name": CI_action_name,
            "source_stage_name": CI_stage_name
        })

    def add_build_stage(self, repo: dict):
        build_project = codebuild.PipelineProject(self._scope, f"{repo['name']}BuildProject",
            build_spec=self.create_build_spec())
        build_action = codepipeline_actions.CodeBuildAction(
            action_name=f"{repo['name']}_Build",
            project=build_project,
            input=repo['source_output'],
            outputs=[codepipeline.Artifact(f"{repo['name']}_BuildOutput")]
        )
        self._pipeline.add_stage(stage_name=f"{repo['name']}_BuildStage", actions=[build_action])
        repo['build_project_name'] = build_project.project_name

    def add_manual_approval_stage(self):
        manual_approval_action = codepipeline_actions.ManualApprovalAction(
            action_name="ManualApproval",
            additional_information="Approve the change to continue deployment",
            #run_order=2
        )
        self._pipeline.add_stage(
            stage_name="ManualApproval",
            actions=[manual_approval_action]
        )
        
    def create_build_spec(self):
        return codebuild.BuildSpec.from_object({
            "version": "0.2",
            "phases": {
                "install": {
                    "runtime-versions": {
                        "python": "3.8"
                    },
                    "commands": [
                        "echo Installing necessary packages...",
                        #"pip install -r requirements.txt" # example install command
                    ]
                },
                "pre_build": {
                    "commands": [
                        "echo Preparing build...",
                        #"pytest tests/" # example test command
                    ]
                },
                "build": {
                    "commands": [
                        "echo Starting build...",
                        #"sam build" # example build command
                    ]
                }
            },
            "artifacts": {"files": []}
        })        