# Project Structure

```
.
├── app.py                 # CDK app entry point
├── cdk.json               # CDK configuration and context
├── stacks/                # CDK stack definitions
│   └── apigw_http_api_lambda_dynamodb_python_cdk_stack.py
├── lambda/                # Lambda function code
│   └── apigw-handler/
│       └── index.py       # API Gateway handler
├── docs/                  # Architecture diagrams
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Development dependencies
└── example-pattern.json   # Serverless pattern metadata
```

## Key Conventions

### Stack Organization
- One main stack in `stacks/` directory
- Stack class naming: `<Service>Stack` pattern
- Constants (e.g., `TABLE_NAME`) defined at module level

### Lambda Functions
- Each Lambda in its own subdirectory under `lambda/`
- Entry point: `index.py` with `handler` function
- Use environment variables for configuration (e.g., `TABLE_NAME`)

### CDK Patterns
- Import CDK modules with aliases (e.g., `aws_dynamodb as dynamodb_`)
- Use L2 constructs where available
- Grant permissions using built-in methods (e.g., `table.grant_write_data()`)
