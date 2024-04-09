import json, os
import requests
import boto3
import logging
from botocore.exceptions import ClientError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def handler(event, context):
    print("Received event:", json.dumps(event, indent=2))
    
    # Extract information from the event
    repo_name = event['repo_name']
    message = event['message']
    status = event['status']
    context_message = event['context']
    pipeline_name = event['pipeline_name']
    source_stage_name = event['source_stage_name']
    source_action_name = event['source_action_name']

    owner = os.environ.get('GITHUB_REPO_OWNER')
    event_details = getEventDetails(pipeline_name, source_stage_name, source_action_name, owner, repo_name, message, context_message)

    # Bot token and channel ID
    bot_token = get_discord_secret()
    target_channel_id = '1194790525258190908'  # channel id for #build-statuses

    response = send_discord_message(target_channel_id, event_details, bot_token)
    print(response)

    return {
        "statusCode": 200,
        "body": json.dumps(f"Message sent to Discord: {event_details}")
    }

def get_discord_secret():
    """
    Retrieves the secret value from AWS Secrets Manager.

    Returns:
        str: The Personal Access Token (PAT) stored in the secret.
    
    Raises:
        ClientError: If there is an error retrieving the secret.
    """
    secret_name = "github/discord_build_statuses/PAP"
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

def send_discord_message(channel_id, message, bot_token):
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
    headers = {
        "Authorization": f"Bot {bot_token}",
        "Content-Type": "application/json"
    }
    data = {
        "content": message
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Error sending Discord message: {e}")
        raise e

def getEventDetails(pipeline_name, source_stage_name, source_action_name, owner, repo_name, message, context_message):
    """
    Retrieves the event details from the environment variables.

    Returns:
        dict: A dictionary containing the event details.
    """
    commit_sha = get_commit_sha(pipeline_name, source_stage_name, source_action_name)
    if commit_sha is None:
        logger.error("Failed to retrieve commit SHA")
        return None
    
    url = f"https://www.github.com/{owner}/{repo_name}/commit/{commit_sha}"

    return f"{message}\n{'-' * 10}\nContext: {context_message}\nCommit SHA: {commit_sha}\nCommit URL: {url}"

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