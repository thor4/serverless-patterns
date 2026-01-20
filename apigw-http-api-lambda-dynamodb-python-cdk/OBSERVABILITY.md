# Serverless Observability Implementation

This document describes the observability features added to the apigw-http-api-lambda-dynamodb-python-cdk pattern.

## Overview

Comprehensive observability has been implemented using AWS Lambda Powertools for Python, providing:

- **Structured JSON Logging**: All logs are emitted in JSON format with correlation IDs for tracing requests across services
- **Custom CloudWatch Metrics**: Request latency, error rates, and DynamoDB operation metrics
- **X-Ray Tracing**: Distributed tracing across API Gateway, Lambda, and DynamoDB with custom subsegments
- **Health Endpoint**: `/health` endpoint for monitoring application health and DynamoDB connectivity

## Features

### 1. Structured Logging

All logs include:
- `timestamp`: ISO8601 formatted timestamp
- `level`: Log level (INFO, ERROR, etc.)
- `message`: Log message
- `service`: Service name ("serverless-api")
- `correlation_id`: AWS request ID for correlating logs
- `xray_trace_id`: X-Ray trace ID when tracing is active
- Contextual information (table name, operation type, etc.)

Example log entry:
```json
{
    "timestamp": "2024-01-15T10:30:00.000Z",
    "level": "INFO",
    "message": "Processing POST request to /",
    "service": "serverless-api",
    "correlation_id": "abc123-def456",
    "xray_trace_id": "1-abc123-def456789",
    "cold_start": false
}
```

### 2. Custom Metrics

The following metrics are emitted to CloudWatch:

| Metric Name | Unit | Dimensions | Description |
|-------------|------|------------|-------------|
| `RequestLatency` | Milliseconds | endpoint, method | Total request processing time |
| `DynamoDBLatency` | Milliseconds | operation, table | DynamoDB operation duration |
| `SuccessfulRequests` | Count | endpoint | Successful request count (2xx) |
| `ClientErrors` | Count | endpoint, status_code | Client error count (4xx) |
| `ServerErrors` | Count | endpoint, status_code | Server error count (5xx) |
| `ColdStart` | Count | function_name | Cold start occurrences |

All metrics are in the `ServerlessApp` namespace.

### 3. X-Ray Tracing

X-Ray tracing is enabled on:
- API Gateway stage
- Lambda function
- Custom subsegments for:
  - POST request handling
  - Health check execution
  - DynamoDB operations

Traces include annotations for searchable metadata (table name, operation type, item ID).

### 4. Health Endpoint

**Endpoint**: `GET /health`

**Healthy Response** (200):
```json
{
    "status": "healthy",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "checks": {
        "dynamodb": {
            "status": "healthy",
            "latency_ms": 45.2,
            "table_name": "demo_table"
        }
    },
    "version": "1.0.0"
}
```

**Unhealthy Response** (503):
```json
{
    "status": "unhealthy",
    "timestamp": "2024-01-15T10:30:00.000Z",
    "checks": {
        "dynamodb": {
            "status": "unhealthy",
            "error": "Connection timeout",
            "table_name": "demo_table"
        }
    },
    "version": "1.0.0"
}
```

## Infrastructure Changes

### CDK Stack Updates

1. **Lambda Powertools Layer**: Added AWS Lambda Powertools Python v3 layer (Python 3.10 compatible)
2. **X-Ray Tracing**: Enabled on both Lambda function and API Gateway stage
3. **Environment Variables**:
   - `POWERTOOLS_SERVICE_NAME`: "serverless-api"
   - `POWERTOOLS_METRICS_NAMESPACE`: "ServerlessApp"
   - `LOG_LEVEL`: "INFO"
4. **Health Endpoint**: Added `/health` resource with GET method to API Gateway
5. **IAM Permissions**: Granted DynamoDB DescribeTable permission for health checks

### Lambda Runtime

Changed from Python 3.14 to Python 3.10 to match the maximum supported runtime version for CDK 2.77.0 and Lambda Powertools compatibility.

## Backward Compatibility

The existing POST endpoint functionality remains unchanged:

- **POST /** with valid JSON body writes data to DynamoDB
- **POST /** without body writes default data
- Response format maintains the existing structure with `message` field

## Testing

Comprehensive test suite includes:

### Unit Tests
- CDK stack configuration
- Lambda handler functionality
- Health endpoint behavior
- Error handling

### Property-Based Tests
Using Hypothesis for property testing with 100+ iterations:

- **Logging Properties** (1-6): Log structure, correlation IDs, context
- **Metrics Properties** (7-12): Metric emission for various scenarios
- **Tracing Properties** (13-15): Trace subsegments and exception capture
- **Handler Properties** (16-17): Health check and data persistence

### Running Tests

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/

# Run only unit tests
pytest tests/unit/

# Run only property tests
pytest tests/property/

# Run with verbose output
pytest -v tests/

# Run specific test file
pytest tests/unit/test_cdk_stack.py
```

## Deployment

```bash
# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Synthesize CloudFormation template
cdk synth

# Deploy stack
cdk deploy

# Deploy with specific AWS profile
cdk deploy --profile <profile-name>
```

## Monitoring

### CloudWatch Logs
View structured JSON logs in CloudWatch Logs console:
1. Navigate to CloudWatch > Log groups
2. Find `/aws/lambda/apigw_handler`
3. Use CloudWatch Logs Insights for querying:

```sql
fields @timestamp, message, correlation_id, status_code, duration_ms
| filter level = "ERROR"
| sort @timestamp desc
```

### CloudWatch Metrics
View custom metrics in CloudWatch Metrics console:
1. Navigate to CloudWatch > Metrics > All metrics
2. Select `ServerlessApp` namespace
3. View metrics by dimensions (endpoint, method, status_code, etc.)

### X-Ray Traces
View distributed traces in X-Ray console:
1. Navigate to X-Ray > Traces
2. Filter by service name "serverless-api"
3. Analyze service map and trace details

## Requirements Fulfilled

All requirements from the specification are implemented:

### Requirement 1: Structured JSON Logging ✅
- JSON logs with correlation IDs
- X-Ray trace ID inclusion
- Contextual information for DynamoDB operations
- Response logging with status codes and duration
- Error logging with stack traces

### Requirement 2: Custom CloudWatch Metrics ✅
- Request latency metrics
- Client error metrics (4xx)
- Server error metrics (5xx)
- DynamoDB operation latency
- Successful request metrics
- Consistent namespace "ServerlessApp"

### Requirement 3: X-Ray Tracing ✅
- Lambda X-Ray tracing enabled
- API Gateway X-Ray tracing enabled
- DynamoDB operation subsegments
- Business logic subsegments
- Exception capture in traces

### Requirement 4: Health Endpoint ✅
- GET /health endpoint
- DynamoDB connectivity check
- 200 response when healthy
- 503 response when unhealthy
- Duration included in response

### Requirement 5: Infrastructure Updates ✅
- Lambda Powertools layer
- Environment variables configured
- X-Ray permissions granted
- /health endpoint in API Gateway
- Backward compatibility maintained

### Requirement 6: Backward Compatibility ✅
- POST with valid body writes to DynamoDB
- POST without body writes defaults
- Response format unchanged

## References

- [AWS Lambda Powertools Python](https://docs.powertools.aws.dev/lambda/python/)
- [AWS X-Ray Documentation](https://docs.aws.amazon.com/xray/)
- [CloudWatch Embedded Metric Format](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/CloudWatch_Embedded_Metric_Format.html)
- [AWS CDK Python](https://docs.aws.amazon.com/cdk/api/v2/python/)
