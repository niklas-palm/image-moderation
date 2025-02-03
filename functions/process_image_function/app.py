import json
import os
import boto3
import json
import base64

from aws_lambda_powertools import Logger

# Set up logging
logger = Logger()

# Environment variables
IMAGE_BUCKET = os.environ["IMAGE_BUCKET"]

s3_client = boto3.client("s3")
bedrock = boto3.client(
    service_name="bedrock-runtime",
    region_name="us-west-2",
)

# MODEL_ID = "us.amazon.nova-lite-v1:0"
MODEL_ID = "us.amazon.nova-pro-v1:0"


def get_prompt_payload(image_base64, prompt, filetype, prefill=None):
    content = []

    # Add image
    content.append(
        {
            "image": {
                "format": filetype,
                "source": {"bytes": image_base64},
            }
        }
    )

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

    print("\n")
    return json.dumps(prompt_config)


def invoke_model(image_base64, prompt, filetype, prefill=None):
    payload = get_prompt_payload(image_base64, prompt, filetype, prefill=prefill)
    response = bedrock.invoke_model(
        body=payload,
        modelId=MODEL_ID,
    )

    return json.loads(response.get("body").read())


def get_completion_from_response(response):
    return response["output"]["message"]["content"][0]["text"]


def lambda_handler(event, context):
    try:
        payload = event["Payload"]
        logger.info(payload)

        prompt = payload["prompt"]
        s3_image_key = payload["image_key"]
        filetype = os.path.splitext(s3_image_key)[1].lower().replace(".", "")

        # Download image
        response = s3_client.get_object(Bucket=IMAGE_BUCKET, Key=s3_image_key)
        image_binary = response["Body"].read()
        image_base64 = base64.b64encode(image_binary).decode("utf-8")

        logger.info(f"Invoking Bedrock with prompt: {prompt}")

        response = invoke_model(image_base64, prompt, filetype, prefill=None)
        completion = get_completion_from_response(response)

        return {"vote": completion}

    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        raise
