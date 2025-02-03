## Image moderation through voting

Sets up infrastructure to run parallell analysis of images for an image moderation solution through voting.

This solution is appropriate where thorough and careful moderation is necessary, minimizing the concern of each prompt to an LLM to increase the quality of each completion.

### Prerequisites

- AWS CLI
- AWS SAM CLI
- Active AWS credentials in the environment

### Usage

1. Deploy infrastructure

```bash
make go
```

2. Test workflow

```bash
make test-workflow
```
