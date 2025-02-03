.ONESHELL:
SHELL := /bin/bash

# Help function to display available commands
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

# Default target when just running 'make'
.DEFAULT_GOAL := help

# Environment variables with default values
export STACKNAME ?= content-moderation-demo
export REGION ?= us-west-2
export PROJECT ?= content-moderation-demo # tag used for cost tracking
export IMAGE_PATH ?= assets/swaa.jpg
export CONFIG_PATH ?= prompt_config.yml

# Mark targets that don't create files as .PHONY
.PHONY: build deploy delete sync logs logs.tail validate go outputs test-workflow

validate: ## Validates the SAM template
	@echo "Validating SAM template..."
	sam validate \
		--template $(TEMPLATE) \
		--region $(REGION)

build: ## Downloads all dependencies and builds resources
	@echo "Building SAM application..."
	sam build

deploy: ## Deploys the artifacts from the previous build
	@echo "Deploying stack $(STACKNAME) to region $(REGION)..."
	sam deploy \
		--stack-name $(STACKNAME) \
		--resolve-s3 \
		--capabilities CAPABILITY_IAM \
		--region $(REGION) \
		--no-fail-on-empty-changeset \
		--tags project=$(PROJECT)

delete: ## Deletes the CloudFormation stack
	@echo "Deleting stack $(STACKNAME) from region $(REGION)..."
	sam delete \
		--stack-name $(STACKNAME) \
		--region $(REGION) \
		--no-prompts

go: build deploy ## Build and deploys the stack

# Local development commands
sync: ## Enables hot-reloading for local development
	@echo "Starting hot-reloading with resources in stack: $(STACKNAME)"
	sam sync \
		--watch \
		--stack-name $(STACKNAME) \
		--region $(REGION)

logs: ## Fetches the latest logs
	@echo "Fetching latest logs from stack: $(STACKNAME)"
	sam logs \
		--stack-name $(STACKNAME) \
		--region $(REGION)

logs.tail: ## Starts tailing the logs in real-time
	@echo "Starting to tail the logs from stack: $(STACKNAME)"
	sam logs \
		--stack-name $(STACKNAME) \
		--region $(REGION) \
		--tail

# Test commands
outputs: ## Fetch CloudFormation outputs and store them in .env file
	@echo "Fetching CloudFormation outputs..."
	@aws cloudformation describe-stacks \
		--stack-name $(STACKNAME) \
		--region $(REGION) \
		--query 'Stacks[0].Outputs[*].{Key:OutputKey,Value:OutputValue}' \
		--output json > .stack-outputs.json

invoke: outputs ## Invoke the Bedrock agent with a query
	@echo "Invoking Bedrock agent..."
	@python scripts/invoke_agent.py \
		--agent-id $$(jq -r '.[] | select(.Key=="AgentId") | .Value' .stack-outputs.json) \
		--alias-id $$(jq -r '.[] | select(.Key=="AgentAliasID") | .Value' .stack-outputs.json) \
		--region $(REGION) \
		--query "$(query)"

test-workflow: outputs ## Upload image and run state machine workflow
	@echo "Starting workflow test..."
	$(eval STATE_MACHINE_ARN := $(shell cat .stack-outputs.json | jq -r '.[] | select(.Key=="StatemachineARN") | .Value'))
	$(eval IMAGE_BUCKET := $(shell cat .stack-outputs.json | jq -r '.[] | select(.Key=="ImageBucket") | .Value'))
	python test_workflow.py \
		--image-path $(IMAGE_PATH) \
		--bucket $(IMAGE_BUCKET) \
		--state-machine-arn $(STATE_MACHINE_ARN) \
		--config $(CONFIG_PATH) \
		--region $(REGION)