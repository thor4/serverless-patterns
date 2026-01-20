# Tech Stack

## Infrastructure
- **IaC Framework**: AWS CDK (Python)
- **CDK Version**: aws-cdk-lib 2.77.0
- **Constructs**: >=10.0.0, <11.0.0

## Runtime
- **Language**: Python 3.10 (Lambda runtime - CDK 2.77.0 max supported)
- **Lambda Handler**: `lambda/apigw-handler/index.py`

## AWS Services
- Amazon API Gateway (REST API with Lambda proxy)
- AWS Lambda (VPC-deployed)
- Amazon DynamoDB
- Amazon VPC with private subnets
- VPC Gateway Endpoint for DynamoDB

## Development Dependencies
- pytest 6.2.5

## Common Commands

```bash
# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate.bat  # Windows

# Install dependencies
pip install -r requirements.txt

# CDK commands
cdk synth       # Synthesize CloudFormation template
cdk deploy      # Deploy stack
cdk deploy --profile <name>  # Deploy with specific AWS profile
cdk diff        # Compare deployed vs current state
cdk destroy     # Tear down resources
cdk ls          # List stacks
```

## Code Style
- Follow PEP 8 for Python code
- Use type hints where appropriate
- Include copyright headers in source files (MIT-0 license)
