""" 
CI CD Stack
-------------
This stack is responsible for creating the CI/CD pipeline. It uses the AWS CodePipeline construct to create
a pipeline that listens for changes in the GitHub repository and triggers the build and deploy stages.
"""

from constructs import Construct
import os, shutil, sys
from aws_cdk import (
    Stack,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as codepipeline_actions,
    aws_s3 as s3,
    aws_lambda as lambda_,
    aws_codebuild as codebuild,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_logs,
    SecretValue,
    RemovalPolicy,
    Duration
)

class CICDStack(Stack):
    
    def __init__(self, scope: Construct, construct_id: str, repositories: list, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.repositories = repositories
        self.artifact_bucket = self.create_artifact_bucket()
        
        pipeline = self.create_pipeline()
        self.pipeline_name = pipeline.pipeline_name
        
        self.add_stages_to_pipeline(pipeline)
        self.add_lambda_functions(pipeline)
        
    def create_artifact_bucket(self):
        return s3.Bucket(
            self, "ArtifactBucket",
            removal_policy=RemovalPolicy.DESTROY
        )
        
    def create_pipeline(self):
        return codepipeline.Pipeline(
            self, "Pipeline",
            artifact_bucket=self.artifact_bucket,
            #restart_execution_on_update=True,
            pipeline_name="RentalPropertiesAgentCICDPipeline"
        )
    
    def add_stages_to_pipeline(self, pipeline):
        for repo in self.repositories:
            self.add_source_stage(pipeline, repo)
            self.add_manual_approval_stage(pipeline)
            self.add_build_stage(pipeline, repo)
            
    def add_manual_approval_stage(self, pipeline):
        manual_approval_action = codepipeline_actions.ManualApprovalAction(
            action_name="ManualApproval",
            additional_information="Approve the change to continue deployment",
            #run_order=2
        )
        pipeline.add_stage(
            stage_name="ManualApproval",
            actions=[manual_approval_action]
        )
        
    def add_source_stage(self, pipeline, repo):
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
        pipeline.add_stage(stage_name=CI_stage_name, actions=[source_action])
        repo.update({
            "source_output": source_output,
            "source_action_name": CI_action_name,
            "source_stage_name": CI_stage_name
        })
        
    def add_build_stage(self, pipeline, repo):
        build_project = codebuild.PipelineProject(self, f"{repo['name']}BuildProject",
            build_spec=self.create_build_spec())
        build_action = codepipeline_actions.CodeBuildAction(
            action_name=f"{repo['name']}_Build",
            project=build_project,
            input=repo['source_output'],
            outputs=[codepipeline.Artifact(f"{repo['name']}_BuildOutput")]
        )
        pipeline.add_stage(stage_name=f"{repo['name']}_BuildStage", actions=[build_action])
        repo['build_project_name'] = build_project.project_name
        
    def create_build_spec(self):
        return codebuild.BuildSpec.from_object({
            "version": "0.2",
            "phases": {
                "install": {"commands": ["echo Installing necessary packages..."]},
                "pre_build": {"commands": ["echo Preparing build..."]},
                "build": {"commands": ["echo Starting build..."]}},
            "artifacts": {"files": []}
        })
        
    def add_lambda_functions(self, pipeline):
        github_lambda = self.create_github_status_lambda(pipeline.pipeline_arn)
        discord_lambda = self.create_discord_notifier_lambda(pipeline.pipeline_arn)
        self.add_status_notifications(github_lambda, discord_lambda)
        
    def add_status_notifications(self, github_lambda, discord_lambda):
        for repo in self.repositories:
            self.create_build_start_rule(repo, github_lambda)
            self.create_build_success_rule(repo, github_lambda, discord_lambda)
            self.create_build_failure_rule(repo, github_lambda, discord_lambda)
            
    def create_build_start_rule(self, repo, github_lambda):
        rule = self.create_eventbridge_rule(
            rule_id=f"{repo['name']}BuildStartRule",
            description="Triggered when a build starts",
            event_pattern={
                "source": ["aws.codebuild"],
                "detail": {
                    "build-status": ["IN_PROGRESS"],
                    "project-name": [repo['build_project_name']]
                }
            }
        )
        # Add GitHub target for build start
        rule.add_target(targets.LambdaFunction(github_lambda, event=events.RuleTargetInput.from_object({
            "repo_name": repo['repo_name'],
            "status": "pending",
            "context": "CodeBuild",
            "pipeline_name": self.pipeline_name,
            "source_stage_name": repo['source_stage_name'],
            "source_action_name": repo['source_action_name'],
        })))

    def create_build_success_rule(self, repo, github_lambda, discord_lambda):
        rule = self.create_eventbridge_rule(
            rule_id=f"{repo['name']}BuildSuccessRule",
            description="Triggered when a build succeeds",
            event_pattern={
                "source": ["aws.codebuild"],
                "detail": {
                    "build-status": ["SUCCEEDED"],
                    "project-name": [repo['build_project_name']]
                }
            }
        )

        # Add GitHub and Discord targets for build success
        rule.add_target(targets.LambdaFunction(github_lambda, event=events.RuleTargetInput.from_object({
            "repo_name": repo['repo_name'],
            "status": "success",
            "context": "CodeBuild",
            "pipeline_name": self.pipeline_name,
            "source_stage_name": repo['source_stage_name'],
            "source_action_name": repo['source_action_name'],
        })))
        rule.add_target(targets.LambdaFunction(discord_lambda, event=events.RuleTargetInput.from_object({
            "repo_name": repo['repo_name'],
            "message": f"Build Succeeded for {repo['repo_name']}",
            "status": "success",
            "context": "CodeBuild",
            "pipeline_name": self.pipeline_name,
            "source_stage_name": repo['source_stage_name'],
            "source_action_name": repo['source_action_name'],
        })))

    def create_build_failure_rule(self, repo, github_lambda, discord_lambda):
        rule = self.create_eventbridge_rule(
            rule_id=f"{repo['name']}BuildFailureRule",
            description="Triggered when a build fails",
            event_pattern={
                "source": ["aws.codebuild"],
                "detail": {
                    "build-status": ["FAILED", "STOPPED"],
                    "project-name": [repo['build_project_name']]
                }
            }
        )

        # Add GitHub and Discord targets for build failure
        rule.add_target(targets.LambdaFunction(github_lambda, event=events.RuleTargetInput.from_object({
            "repo_name": repo['repo_name'],
            "status": "failure",
            "context": "CodeBuild",
            "pipeline_name": self.pipeline_name,
            "source_stage_name": repo['source_stage_name'],
            "source_action_name": repo['source_action_name'],
        })))
        rule.add_target(targets.LambdaFunction(discord_lambda, event=events.RuleTargetInput.from_object({
            "repo_name": repo['repo_name'],
            "message": f"Build Failed for {repo['repo_name']}",
            "status": "failure",
            "context": "CodeBuild",
            "pipeline_name": self.pipeline_name,
            "source_stage_name": repo['source_stage_name'],
            "source_action_name": repo['source_action_name'],
        })))

    def create_eventbridge_rule(self, rule_id, description, event_pattern):
        return events.Rule(self, rule_id, description=description, event_pattern=event_pattern)
    
    def create_github_status_lambda(self, codepipeline_arn):
        source_dir = "rental_properties_agent_cdk/CICD/lambda/github_status"
        self.create_package_directory(source_dir)
        github_status_lambda = lambda_.Function(
            self, "GithubStatusNotifier",
            runtime=lambda_.Runtime.PYTHON_3_8,
            handler="github_status.handler",
            code=lambda_.Code.from_asset(source_dir+"/package"),
            environment={
                'GITHUB_REPO_OWNER': 'CaerusLabs',
            },
            timeout=Duration.seconds(15),
        )

        # Add the necessary permission to the Lambda function's execution role
        github_status_lambda.role.add_to_policy(iam.PolicyStatement(
            actions=["codepipeline:GetPipelineState"],
            resources=[codepipeline_arn]
        ))
        
        github_status_lambda.role.add_to_policy(iam.PolicyStatement(
            actions=["secretsmanager:GetSecretValue"],
            resources=["arn:aws:secretsmanager:us-east-2:260374441616:secret:github/build_status/PAP-YcYH8O"]
        ))
        
        # Grant read access to the artifact bucket
        self.artifact_bucket.grant_read(github_status_lambda)

        # Explicitly set the dependency on the S3 bucket
        github_status_lambda.node.add_dependency(self.artifact_bucket)

        return github_status_lambda
    
    def create_package_directory(self, source_dir):
        package_dir = source_dir+"/package"
        if os.path.exists(package_dir):
            # Remove the package directory and all its contents
            shutil.rmtree(package_dir)

        # Create the package directory
        os.makedirs(package_dir)

        # pip install the required packages
        pip_command = "pip3" if sys.platform == "linux" or sys.platform == "darwin" else "pip"
        os.system(f"{pip_command} install -r {source_dir}/requirements.txt -t {package_dir}")

        # Copy the source files into the package directory
        for filename in os.listdir(source_dir):
            if filename.endswith(".py"):
                shutil.copy(os.path.join(source_dir, filename), package_dir)

        return package_dir
    
    def create_discord_notifier_lambda(self, codepipeline_arn):
        source_dir = "rental_properties_agent_cdk/CICD/lambda/discord_notifier"
        self.create_package_directory(source_dir)
        discord_notifier =  lambda_.Function(
            self, "DiscordNotifier",
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler="discord_notifier.handler",
            code=lambda_.Code.from_asset(source_dir+"/package"),
            environment={
                'GITHUB_REPO_OWNER': 'CaerusLabs',
            },
            timeout=Duration.seconds(15),
        )

        # Add the necessary permission to the Lambda function's execution role
        discord_notifier.role.add_to_policy(iam.PolicyStatement(
            actions=["codepipeline:GetPipelineState"],
            resources=[codepipeline_arn]
        ))
    
        discord_notifier.role.add_to_policy(iam.PolicyStatement(
            actions=["secretsmanager:GetSecretValue"],
            resources=["arn:aws:secretsmanager:us-east-2:260374441616:secret:github/discord_build_statuses/PAP-o7uQEZ"]
        ))

        return discord_notifier