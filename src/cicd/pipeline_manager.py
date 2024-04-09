from src.core.abstracts.pipeline_manager import AbstractPipelineManager, AbstractStageManager
from aws_cdk import (
    Stack,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_s3 as s3,
    aws_lambda as lambda_,
    aws_codebuild as codebuild,
)
from constructs import Construct
from src.core.models.repository import Repository

class PipelineManager(AbstractPipelineManager):
    def __init__(self, scope, StageManagerType: AbstractStageManager, artifact_bucket, pipeline_name, repository_info: Repository, website_bucket: s3.Bucket = None):
        super().__init__(scope, artifact_bucket, pipeline_name)
        self.create_pipeline()
        self.repository_info = repository_info
        self.stage_manager = StageManagerType(self._pipeline, scope)
        self.website_bucket = website_bucket
        
    def configure_pipeline(self):
        """
        Configures the pipeline by adding source, manual approval, and build stages for each repository.

        For each repository in the `repositories` list, this method:
        1. Adds a source stage that pulls the latest code from the repository.
        2. Adds a manual approval stage that pauses the pipeline until manual approval is given.
        3. Adds a build stage that builds the code from the repository.
        """
        self.stage_manager.add_source_stage(self.repository_info)
        self.stage_manager.add_manual_approval_stage()
        self.stage_manager.add_build_stage(self.repository_info)
        if self.repository_info.deployable:
            if not self.website_bucket:
                self.stage_manager.add_deploy_stage(self.repository_info)
            else:
                self.stage_manager.add_deploy_stage(self.repository_info, self.website_bucket)
            
    @property
    def pipeline(self):
        return self._pipeline
            
            
class StageManagerWeb(AbstractStageManager):
    def __init__(self, pipeline: codepipeline.Pipeline, scope: Construct):
        super().__init__(pipeline, scope)
        self.build_artifact_out = codepipeline.Artifact()
    
    def add_source_stage(self, repo: Repository):
        CI_action_name = f"{repo.name}_Source"
        CI_stage_name = f"{repo.name}_SourceStage"
        source_output = codepipeline.Artifact()
        source_action = codepipeline_actions.CodeStarConnectionsSourceAction(
            action_name=CI_action_name,
            connection_arn=repo.code_star_connection_arn,
            owner=repo.owner,
            repo=repo.repo_name,
            output=source_output,
            branch=repo.branch,
            variables_namespace=f"{repo.name}_SourceVariables"
        )
        self._pipeline.add_stage(stage_name=CI_stage_name, actions=[source_action])
        repo.source_output = source_output
        repo.source_action_name = CI_action_name
        repo.source_stage_name = CI_stage_name

    def add_build_stage(self, repo: Repository):
        self.build_artifact_out = codepipeline.Artifact(f"{repo.name}_BuildOutput")
        build_project = codebuild.PipelineProject(
            self._scope, 
            f"{repo.name}BuildProject",
            build_spec=self.create_build_spec(), 
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0
            )
        )
        build_action = codepipeline_actions.CodeBuildAction(
            action_name=f"{repo.name}_Build",
            project=build_project,
            input=repo.source_output,
            outputs=[self.build_artifact_out]
        )
        self._pipeline.add_stage(stage_name=f"{repo.name}_BuildStage", actions=[build_action])
        repo.build_project_name = build_project.project_name

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
        
    def add_deploy_stage(self, repo: Repository, website_bucket: s3.Bucket):
        deploy_action = codepipeline_actions.S3DeployAction(
            action_name=f"{repo.name}Deploy",
            input=self.build_artifact_out,
            bucket=website_bucket,
            extract=True
        )
        self._pipeline.add_stage(stage_name=f"{repo.name}DeployStage", actions=[deploy_action])
        
    def create_build_spec(self):
        # return codebuild.BuildSpec.from_object({
        #     "version": "0.2",
        #     "phases": {
        #         "install": {
        #             "runtime-versions": {
        #                 "python": "3.8"
        #             },
        #             "commands": [
        #                 "echo Installing necessary packages...",
        #                 #"pip install -r requirements.txt" # example install command
        #             ]
        #         },
        #         "pre_build": {
        #             "commands": [
        #                 "echo Preparing build...",
        #                 #"pytest tests/" # example test command
        #             ]
        #         },
        #         "build": {
        #             "commands": [
        #                 "echo Starting build...",
        #                 #"sam build" # example build command
        #             ]
        #         }
        #     },
        #     "artifacts": {"files": []}
        # })        
        return codebuild.BuildSpec.from_object({
            "version": "0.2",
            "phases": {
                "install": {
                    "runtime-versions": {
                        "nodejs": "18"  # Nuxt 3 supports Node.js 14 or later; using 16 as an example
                    },
                    "commands": [
                        "echo Installing Node.js dependencies...",
                        "npm install -g npm@latest",
                        "npm install",
                        "npm run postinstall"  # Ensure all necessary preparations are made
                    ]
                },
                "pre_build": {
                    "commands": [
                        "echo Running tests...",
                        # Add commands to run tests if required
                    ]
                },
                "build": {
                    "commands": [
                        "echo Building the Nuxt application...",
                        "npm run generate:dev",
                    ]
                }
            },
            "artifacts": {
                "base-directory": ".output/public",  # Nuxt 3 output directory for `nuxt generate` or `nuxt build`
                "files": [
                    "**/*"
                ]
            }
        })
        
class StageManagerMT(AbstractStageManager):
    def __init__(self, pipeline: codepipeline.Pipeline, scope: Construct):
        super().__init__(pipeline, scope)
        self.build_artifact_out = codepipeline.Artifact()
    
    def add_source_stage(self, repo: Repository):
        CI_action_name = f"{repo.name}_Source"
        CI_stage_name = f"{repo.name}_SourceStage"
        source_output = codepipeline.Artifact()
        source_action = codepipeline_actions.CodeStarConnectionsSourceAction(
            action_name=CI_action_name,
            connection_arn=repo.code_star_connection_arn,
            owner=repo.owner,
            repo=repo.repo_name,
            output=source_output,
            branch=repo.branch,
            variables_namespace=f"{repo.name}_SourceVariables"
        )
        self._pipeline.add_stage(stage_name=CI_stage_name, actions=[source_action])
        repo.source_output = source_output
        repo.source_action_name = CI_action_name
        repo.source_stage_name = CI_stage_name

    def add_build_stage(self, repo: Repository):
        self.build_artifact_out = codepipeline.Artifact(f"{repo.name}_BuildOutput")
        build_project = codebuild.PipelineProject(
            self._scope, 
            f"{repo.name}BuildProject",
            build_spec=self.create_build_spec(), 
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0
            )
        )
        build_action = codepipeline_actions.CodeBuildAction(
            action_name=f"{repo.name}_Build",
            project=build_project,
            input=repo.source_output,
            outputs=[self.build_artifact_out]
        )
        self._pipeline.add_stage(stage_name=f"{repo.name}_BuildStage", actions=[build_action])
        repo.build_project_name = build_project.project_name

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
        
    def add_deploy_stage(self, repo: Repository):
        # Here we would add a deploy action for the MT repo
        # Deployment to lambda function, etc.
        pass
        
    def create_build_spec(self):
        # return codebuild.BuildSpec.from_object({
        #     "version": "0.2",
        #     "phases": {
        #         "install": {
        #             "runtime-versions": {
        #                 "python": "3.8"
        #             },
        #             "commands": [
        #                 "echo Installing necessary packages...",
        #                 #"pip install -r requirements.txt" # example install command
        #             ]
        #         },
        #         "pre_build": {
        #             "commands": [
        #                 "echo Preparing build...",
        #                 #"pytest tests/" # example test command
        #             ]
        #         },
        #         "build": {
        #             "commands": [
        #                 "echo Starting build...",
        #                 #"sam build" # example build command
        #             ]
        #         }
        #     },
        #     "artifacts": {"files": []}
        # })        
        return codebuild.BuildSpec.from_object({
            "version": "0.2",
            "phases": {
                "install": {
                    "runtime-versions": {
                        "python": "3.9"
                    },
                    "commands": [
                        "echo Installing some dependencies...",
                        "echo Finished installing dependencies..."
                    ]
                },
                "pre_build": {
                    "commands": [
                        "echo Running tests...",
                        # Add commands to run tests if required
                    ]
                },
                "build": {
                    "commands": [
                        "echo Building the application...",
                        "python3 scripts/package_fastapi.py dev",
                        "echo Finished building the application..."
                    ]
                }
            },
            "artifacts": {
                "base-directory": "dist/",  # Output directory for the build
                "files": [
                    "**/*"
                ]
            }
        })