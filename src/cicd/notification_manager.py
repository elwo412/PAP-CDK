from src.core.abstracts.notification_manager import AbstractNotificationManager
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
from src.core.models.repository import Repository

class NotificationManager(AbstractNotificationManager):
    
    def __init__(self, scope, pipeline_name):
        super().__init__(scope, pipeline_name)

    def create_build_success_rule(self, repo: Repository, github_lambda, discord_lambda):
        rule_id = f"{repo.name}BuildSuccessRule"
        description = "Triggered when a build succeeds"
        event_pattern = {
            "source": ["aws.codebuild"],
            "detail": {
                "build-status": ["SUCCEEDED"],
                "project-name": [repo.build_project_name]
            }
        }

        github_target = targets.LambdaFunction(github_lambda, event=events.RuleTargetInput.from_object({
            "repo_name": repo.repo_name,
            "status": "success",
            "context": "CodeBuild",
            "pipeline_name": self.pipeline_name,
            "source_stage_name": repo.source_stage_name,
            "source_action_name": repo.source_action_name,
        }))

        discord_target = targets.LambdaFunction(discord_lambda, event=events.RuleTargetInput.from_object({
            "repo_name": repo.repo_name,
            "message": f"Build Succeeded for {repo.repo_name}",
            "status": "success",
            "context": "CodeBuild",
            "pipeline_name": self.pipeline_name,
            "source_stage_name": repo.source_stage_name,
            "source_action_name": repo.source_action_name,
        }))

        return self.create_notification_rule(rule_id, [github_target, discord_target], {'description': description, 'event_pattern': event_pattern})
    
    def create_build_failure_rule(self, repo: Repository, github_lambda, discord_lambda):
        rule_id=f"{repo.name}BuildFailureRule"
        description="Triggered when a build fails"
        event_pattern={
                "source": ["aws.codebuild"],
                "detail": {
                    "build-status": ["FAILED", "STOPPED"],
                    "project-name": [repo.build_project_name]
                }
            }

        # Add GitHub and Discord targets for build failure
        github_target = targets.LambdaFunction(github_lambda, event=events.RuleTargetInput.from_object({
            "repo_name": repo.repo_name,
            "status": "failure",
            "context": "CodeBuild",
            "pipeline_name": self.pipeline_name,
            "source_stage_name": repo.source_stage_name,
            "source_action_name": repo.source_action_name,
        }))
        discord_target = targets.LambdaFunction(discord_lambda, event=events.RuleTargetInput.from_object({
            "repo_name": repo.repo_name,
            "message": f"Build Failed for {repo.repo_name}",
            "status": "failure",
            "context": "CodeBuild",
            "pipeline_name": self.pipeline_name,
            "source_stage_name": repo.source_stage_name,
            "source_action_name": repo.source_action_name,
        }))
        
        return self.create_notification_rule(rule_id, [github_target, discord_target], {'description': description, 'event_pattern': event_pattern})
    
    def create_build_start_rule(self, repo: Repository, github_lambda):
        rule_id=f"{repo.name}BuildStartRule"
        description="Triggered when a build starts"
        event_pattern={
            "source": ["aws.codebuild"],
            "detail": {
                "build-status": ["IN_PROGRESS"],
                "project-name": [repo.build_project_name]
            }
        }
        # Add GitHub target for build start
        github_target = targets.LambdaFunction(github_lambda, event=events.RuleTargetInput.from_object({
            "repo_name": repo.repo_name,
            "status": "pending",
            "context": "CodeBuild",
            "pipeline_name": self.pipeline_name,
            "source_stage_name": repo.source_stage_name,
            "source_action_name": repo.source_action_name,
        }))
        
        return self.create_notification_rule(rule_id, [github_target], {'description': description, 'event_pattern': event_pattern})