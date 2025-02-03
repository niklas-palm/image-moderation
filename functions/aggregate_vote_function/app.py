import json
import boto3

from aws_lambda_powertools import Logger

# Set up logging
logger = Logger()

# Initialize AWS clients
bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-west-2",
)

MODEL_ID = "us.amazon.nova-lite-v1:0"
# MODEL_ID = "us.amazon.nova-pro-v1:0"


def get_prompt_payload(prompt, prefill=None):
    content = []

    # Add prompt
    content.append({"text": prompt})

    messages = [
        {
            "role": "user",
            "content": content,
        }
    ]

    if prefill:
        logger.info("** Prefilling the reponse")
        messages.append(
            {
                "role": "assistant",
                "content": [{"text": prefill}],
            }
        )

    prompt_config = {
        "inferenceConfig": {"temperature": 0},
        "messages": messages,
    }

    return json.dumps(prompt_config)


def invoke_model(prompt, prefill=None):
    payload = get_prompt_payload(prompt, prefill=prefill)
    response = bedrock.invoke_model(
        body=payload,
        modelId=MODEL_ID,
    )

    return json.loads(response.get("body").read())


def get_completion_from_response(response):
    return response["output"]["message"]["content"][0]["text"]


def get_prompt(votes):
    return f"""
## Instruction
You are a vote aggregationg tool for an image content moderation solution. You will carefully analyse the 
provided votes in ## votes and if any of the each individual votes indicates that the content should be 
moderated, you will state so, including the reason why.

## votes
{votes}

## Task
Aggregate the votes above and create a final vote on weather or not the content should be moderated or not.
"""


def lambda_handler(event, context):

    try:
        votes_list = event["Payload"]
        logger.info(votes_list)

        prompt = get_prompt(votes_list)
        response = invoke_model(prompt, prefill=None)
        completion = get_completion_from_response(response)

        return {"aggregated_vote": completion}

    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        raise
