## Image moderation through voting

Sets up infrastructure to run parallell analysis of images for an image moderation solution through voting.

This solution is appropriate where thorough and careful moderation is necessary, minimizing the concern of each prompt to an LLM to increase the quality of each completion. Each prompt is applied in parallell to a given image, analysing the image. The final step of the pipeline aggregates each individual vote for a final moderation decision.

### Prerequisites

- AWS CLI
- AWS SAM CLI
- Active AWS credentials in the environment
- Amazon Nova lite enabled in us-west-2

### Usage

0. Update `prompt_config.yml` with your desired prompts

The solution will apply each prompt in the `prompt_config.yml` to the input image in parallell ( [level of parallelism decided here](statemachine/content_moderation_voting.asl.yaml) )

1. Deploy infrastructure

```bash
make go
```

2. Test workflow

```bash
make test-workflow
```
