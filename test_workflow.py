import argparse
import json
import time
import boto3
import os
import yaml


def load_config(config_path):
    """Load configuration from YAML file"""
    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def upload_image(s3_client, image_path, bucket):
    """Upload image to S3 and return the key"""
    image_key = os.path.basename(image_path)
    s3_client.upload_file(image_path, bucket, image_key)
    return image_key


def start_execution(sfn_client, state_machine_arn, image_key, prompts):
    """Start state machine execution and return the execution ARN"""
    # Format the input as a list of dictionaries, one for each prompt
    input_data = [{"image_key": image_key, "prompt": prompt} for prompt in prompts]

    response = sfn_client.start_execution(
        stateMachineArn=state_machine_arn,
        input=json.dumps(input_data),  # Send the array directly
    )
    return response["executionArn"]


def poll_execution(sfn_client, execution_arn):
    """Poll execution until completion and return the output"""
    while True:
        response = sfn_client.describe_execution(executionArn=execution_arn)
        status = response["status"]

        if status == "SUCCEEDED":
            print("Execution completed successfully!")
            return json.loads(response["output"])
        elif status in ["FAILED", "TIMED_OUT", "ABORTED"]:
            print(f"Execution failed with status: {status}")
            raise Exception(
                f"State machine execution failed: {response.get('error', 'Unknown error')}"
            )

        print(f"Status: {status}")
        time.sleep(2)


def main():
    parser = argparse.ArgumentParser(description="Run workflow test")
    parser.add_argument("--image-path", required=True, help="Path to image file")
    parser.add_argument("--bucket", required=True, help="S3 bucket name")
    parser.add_argument("--state-machine-arn", required=True, help="State machine ARN")
    parser.add_argument("--config", default="config.yml", help="Path to config file")
    parser.add_argument("--region", default="us-west-2", help="AWS region")

    args = parser.parse_args()

    # Load configuration
    try:
        config = load_config(args.config)
        prompts = config.get("prompts", [])
        if not prompts:
            raise ValueError("No prompts found in config file")
    except Exception as e:
        print(f"Error loading config: {str(e)}")
        exit(1)

    # Initialize AWS clients
    s3_client = boto3.client("s3", region_name=args.region)
    sfn_client = boto3.client("stepfunctions", region_name=args.region)

    try:
        # Upload image
        print(f"Uploading image {args.image_path} to bucket {args.bucket}...")
        image_key = upload_image(s3_client, args.image_path, args.bucket)

        # Print prompts that will be used
        print("\nUsing the following prompts:")
        for i, prompt in enumerate(prompts, 1):
            print(f"{i}. {prompt}")

        # Start execution
        print("\nStarting state machine execution...")
        execution_arn = start_execution(
            sfn_client, args.state_machine_arn, image_key, prompts
        )
        print(f"Execution ARN: {execution_arn}")

        # Poll until completion
        print("Waiting for execution to complete...")
        output = poll_execution(sfn_client, execution_arn)

        # Print results
        print("\nExecution Results:")
        print(json.dumps(output, indent=2))

    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
