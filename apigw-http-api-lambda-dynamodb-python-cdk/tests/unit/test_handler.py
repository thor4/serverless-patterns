# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Unit tests for Lambda handler.

Feature: serverless-observability
Tests: Requirements 6.1, 6.2, 6.3
"""

import json
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from moto import mock_dynamodb
import boto3


# Mock Lambda context
class MockLambdaContext:
    def __init__(self, request_id="test-request-id"):
        self.aws_request_id = request_id
        self.function_name = "test-function"
        self.memory_limit_in_mb = 1024
        self.invoked_function_arn = "arn:aws:lambda:us-east-1:123456789012:function:test"


@pytest.fixture
def mock_env():
    """Mock environment variables."""
    with patch.dict(os.environ, {"TABLE_NAME": "test_table"}):
        yield


@pytest.fixture
def dynamodb_table():
    """Create mock DynamoDB table."""
    with mock_dynamodb():
        dynamodb = boto3.client("dynamodb", region_name="us-east-1")
        dynamodb.create_table(
            TableName="test_table",
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST"
        )
        yield dynamodb


def test_post_request_with_valid_body(mock_env, dynamodb_table):
    """Test POST request with valid JSON body writes to DynamoDB."""
    # Import after environment is mocked
    import sys
    import importlib
    
    # Add lambda directory to path
    lambda_path = "/projects/sandbox/serverless-patterns/apigw-http-api-lambda-dynamodb-python-cdk/lambda/apigw-handler"
    if lambda_path not in sys.path:
        sys.path.insert(0, lambda_path)
    
    # Import handler
    import index
    if 'index' in sys.modules:
        importlib.reload(index)
    
    event = {
        "httpMethod": "POST",
        "path": "/",
        "body": json.dumps({
            "year": 2024,
            "title": "Test Movie",
            "id": "test-id-123"
        }),
        "requestContext": {
            "requestId": "test-request-id"
        }
    }
    
    context = MockLambdaContext()
    
    response = index.handler(event, context)
    
    # Verify response
    assert response["statusCode"] == 200
    assert "message" in json.loads(response["body"])
    
    # Verify data was written to DynamoDB
    result = dynamodb_table.get_item(
        TableName="test_table",
        Key={"id": {"S": "test-id-123"}}
    )
    assert "Item" in result
    assert result["Item"]["year"]["N"] == "2024"
    assert result["Item"]["title"]["S"] == "Test Movie"


def test_post_request_without_body(mock_env, dynamodb_table):
    """Test POST request without body writes default data."""
    import sys
    import importlib
    
    lambda_path = "/projects/sandbox/serverless-patterns/apigw-http-api-lambda-dynamodb-python-cdk/lambda/apigw-handler"
    if lambda_path not in sys.path:
        sys.path.insert(0, lambda_path)
    
    import index
    if 'index' in sys.modules:
        importlib.reload(index)
    
    event = {
        "httpMethod": "POST",
        "path": "/",
        "body": None,
        "requestContext": {
            "requestId": "test-request-id"
        }
    }
    
    context = MockLambdaContext()
    
    response = index.handler(event, context)
    
    # Verify response format
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "message" in body
    assert body["message"] == "Successfully inserted data!"


def test_post_request_invalid_json(mock_env, dynamodb_table):
    """Test POST request with invalid JSON returns 400."""
    import sys
    import importlib
    
    lambda_path = "/projects/sandbox/serverless-patterns/apigw-http-api-lambda-dynamodb-python-cdk/lambda/apigw-handler"
    if lambda_path not in sys.path:
        sys.path.insert(0, lambda_path)
    
    import index
    if 'index' in sys.modules:
        importlib.reload(index)
    
    event = {
        "httpMethod": "POST",
        "path": "/",
        "body": "invalid json {",
        "requestContext": {
            "requestId": "test-request-id"
        }
    }
    
    context = MockLambdaContext()
    
    response = index.handler(event, context)
    
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Invalid JSON" in body["message"]


def test_post_request_missing_required_field(mock_env, dynamodb_table):
    """Test POST request with missing required field returns 400."""
    import sys
    import importlib
    
    lambda_path = "/projects/sandbox/serverless-patterns/apigw-http-api-lambda-dynamodb-python-cdk/lambda/apigw-handler"
    if lambda_path not in sys.path:
        sys.path.insert(0, lambda_path)
    
    import index
    if 'index' in sys.modules:
        importlib.reload(index)
    
    event = {
        "httpMethod": "POST",
        "path": "/",
        "body": json.dumps({
            "year": 2024,
            "title": "Test Movie"
            # Missing 'id' field
        }),
        "requestContext": {
            "requestId": "test-request-id"
        }
    }
    
    context = MockLambdaContext()
    
    response = index.handler(event, context)
    
    assert response["statusCode"] == 400
    body = json.loads(response["body"])
    assert "Missing required field" in body["message"]


def test_get_request_unknown_path_returns_404(mock_env, dynamodb_table):
    """Test GET request to unknown path returns 404."""
    import sys
    import importlib
    
    lambda_path = "/projects/sandbox/serverless-patterns/apigw-http-api-lambda-dynamodb-python-cdk/lambda/apigw-handler"
    if lambda_path not in sys.path:
        sys.path.insert(0, lambda_path)
    
    import index
    if 'index' in sys.modules:
        importlib.reload(index)
    
    event = {
        "httpMethod": "GET",
        "path": "/unknown",
        "requestContext": {
            "requestId": "test-request-id"
        }
    }
    
    context = MockLambdaContext()
    
    response = index.handler(event, context)
    
    assert response["statusCode"] == 404


def test_response_format_includes_headers(mock_env, dynamodb_table):
    """Test that responses include proper headers."""
    import sys
    import importlib
    
    lambda_path = "/projects/sandbox/serverless-patterns/apigw-http-api-lambda-dynamodb-python-cdk/lambda/apigw-handler"
    if lambda_path not in sys.path:
        sys.path.insert(0, lambda_path)
    
    import index
    if 'index' in sys.modules:
        importlib.reload(index)
    
    event = {
        "httpMethod": "POST",
        "path": "/",
        "body": None,
        "requestContext": {
            "requestId": "test-request-id"
        }
    }
    
    context = MockLambdaContext()
    
    response = index.handler(event, context)
    
    assert "headers" in response
    assert response["headers"]["Content-Type"] == "application/json"
