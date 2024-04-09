import json
import requests
import os
import boto3
import logging
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    """
    Lambda function handler for updating GitHub status.

    Args:
        event (dict): The event data passed to the Lambda function.
        context (object): The runtime information of the Lambda function.

    Returns:
        dict: The response data returned by the Lambda function.
    """
    
    # Log the received event
    logger.info(f"Received event: {json.dumps(event, indent=2)}")

    # Extract information from the event
    repo_name = event['repo_name']
    status = event['status']
    context_message = event['context']
    pipeline_name = event['pipeline_name']
    source_stage_name = event['source_stage_name']
    source_action_name = event['source_action_name']

    # Get the commit SHA from the pipeline state
    commit_sha = get_commit_sha(pipeline_name, source_stage_name, source_action_name)
    if commit_sha is None:
        logger.error("Failed to retrieve commit SHA")
        return {"statusCode": 400, "body": "Error: Missing commit SHA."}

    # Get the GitHub token and owner from secrets and environment variables
    github_token = get_secret()
    owner = os.environ.get('GITHUB_REPO_OWNER')
    if not all([github_token, owner]):
        logger.error("Missing required parameters.")
        return {"statusCode": 400, "body": "Error: Missing required parameters."}

    # Update the GitHub status
    response = update_github_status(github_token, owner, repo_name, commit_sha, status, context_message)
    return response

def get_commit_sha(pipeline_name, source_stage_name, source_action_name):
    """
    Retrieves the commit SHA associated with a specific source action in a CodePipeline.

    Args:
        pipeline_name (str): The name of the CodePipeline.
        source_stage_name (str): The name of the source stage in the CodePipeline.
        source_action_name (str): The name of the source action in the CodePipeline.

    Returns:
        str: The commit SHA associated with the specified source action, or None if an error occurs.
    """
    cp_client = boto3.client('codepipeline')
    try:
        response = cp_client.get_pipeline_state(name=pipeline_name)
        return extract_revision_id_from_response(response, source_stage_name, source_action_name)
    except ClientError as e:
        logger.error(f"Error retrieving pipeline state: {e}")
        return None

def extract_revision_id_from_response(response, source_stage_name, source_action_name):
    """
    Extracts the revision ID from the response object based on the source stage name and action name.

    Args:
        response (dict): The response object containing the stage states and action states.
        source_stage_name (str): The name of the source stage.
        source_action_name (str): The name of the source action.

    Returns:
        str or None: The revision ID if found, None otherwise.
    """
    for stage in response['stageStates']:
        if stage['stageName'] == source_stage_name:
            for action in stage['actionStates']:
                if action['actionName'] == source_action_name and 'currentRevision' in action:
                    return action['currentRevision'].get('revisionId')
    return None

def update_github_status(github_token, owner, repo_name, commit_sha, status, context_message):
    """
    Updates the GitHub status for a specific commit.

    Args:
        github_token (str): The GitHub access token.
        owner (str): The owner of the repository.
        repo_name (str): The name of the repository.
        commit_sha (str): The SHA of the commit.
        status (str): The status to set for the commit. Can be one of "pending", "success", "failure", "error".
        context_message (str): The context message for the status.

    Returns:
        dict: A dictionary containing the response status code and body.
    """
    url = f"https://api.github.com/repos/{owner}/{repo_name}/statuses/{commit_sha}"
    headers = {"Authorization": f"token {github_token}", "Content-Type": "application/json"}
    data = {"state": status, "context": context_message, "description": f"The build status is {status}."}

    try:
        response = requests.post(url, headers=headers, data=json.dumps(data))
        if response.status_code == 201:
            logger.info(f"Successfully updated the status for {commit_sha} in {repo_name}")
            return {"statusCode": 200, "body": json.dumps(f"GitHub status updated for {commit_sha} in {repo_name}")}
        else:
            logger.error(f"Failed to update status: {response.content}")
            return {"statusCode": response.status_code, "body": json.dumps("Failed to update GitHub status")}
    except requests.RequestException as e:
        logger.error(f"Request to GitHub API failed: {e}")
        return {"statusCode": 500, "body": "Error: Request to GitHub API failed."}

def get_secret():
    """
    Retrieves the secret value from AWS Secrets Manager.

    Returns:
        str: The Personal Access Token (PAT) stored in the secret.
    
    Raises:
        ClientError: If there is an error retrieving the secret.
    """
    secret_name = "github/build_status/PAP"
    region_name = "us-east-2"

    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        secret_string = get_secret_value_response['SecretString']
        return json.loads(secret_string)['PAT']
    except ClientError as e:
        logger.error(f"Error retrieving secret: {e}")
        raise e