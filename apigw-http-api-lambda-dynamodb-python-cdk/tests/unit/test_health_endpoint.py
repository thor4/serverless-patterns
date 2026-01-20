# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Unit tests for health endpoint.

Feature: serverless-observability
Tests: Requirements 4.1, 4.2, 4.3, 4.4, 4.5
"""

import json
import os
import pytest
from unittest.mock import Mock, patch
from moto import mock_dynamodb
import boto3


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


def test_health_endpoint_returns_200_when_dynamodb_healthy(mock_env, dynamodb_table):
    """Test health endpoint returns 200 when DynamoDB is accessible."""
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
        "path": "/health",
        "requestContext": {
            "requestId": "test-request-id"
        }
    }
    
    context = MockLambdaContext()
    
    response = index.handler(event, context)
    
    # Verify status code
    assert response["statusCode"] == 200
    
    # Verify response structure
    body = json.loads(response["body"])
    assert body["status"] == "healthy"
    assert "timestamp" in body
    assert "checks" in body
    assert "dynamodb" in body["checks"]
    assert body["checks"]["dynamodb"]["status"] == "healthy"
    assert "latency_ms" in body["checks"]["dynamodb"]
    assert "version" in body


def test_health_endpoint_returns_503_when_dynamodb_unhealthy(mock_env):
    """Test health endpoint returns 503 when DynamoDB is not accessible."""
    import sys
    import importlib
    
    lambda_path = "/projects/sandbox/serverless-patterns/apigw-http-api-lambda-dynamodb-python-cdk/lambda/apigw-handler"
    if lambda_path not in sys.path:
        sys.path.insert(0, lambda_path)
    
    import index
    if 'index' in sys.modules:
        importlib.reload(index)
    
    # Don't create DynamoDB table - will cause connection error
    event = {
        "httpMethod": "GET",
        "path": "/health",
        "requestContext": {
            "requestId": "test-request-id"
        }
    }
    
    context = MockLambdaContext()
    
    response = index.handler(event, context)
    
    # Verify status code
    assert response["statusCode"] == 503
    
    # Verify response structure
    body = json.loads(response["body"])
    assert body["status"] == "unhealthy"
    assert "checks" in body
    assert "dynamodb" in body["checks"]
    assert body["checks"]["dynamodb"]["status"] == "unhealthy"
    assert "error" in body["checks"]["dynamodb"]


def test_health_response_contains_required_fields(mock_env, dynamodb_table):
    """Test health response contains all required fields."""
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
        "path": "/health",
        "requestContext": {
            "requestId": "test-request-id"
        }
    }
    
    context = MockLambdaContext()
    
    response = index.handler(event, context)
    body = json.loads(response["body"])
    
    # Required top-level fields
    assert "status" in body
    assert "timestamp" in body
    assert "checks" in body
    assert "version" in body
    
    # Required check fields
    assert "dynamodb" in body["checks"]
    dynamodb_check = body["checks"]["dynamodb"]
    assert "status" in dynamodb_check
    assert "table_name" in dynamodb_check
    
    # Latency should be present for healthy checks
    if dynamodb_check["status"] == "healthy":
        assert "latency_ms" in dynamodb_check
        assert isinstance(dynamodb_check["latency_ms"], (int, float))
        assert dynamodb_check["latency_ms"] >= 0


def test_health_endpoint_includes_latency(mock_env, dynamodb_table):
    """Test that health check includes latency measurement."""
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
        "path": "/health",
        "requestContext": {
            "requestId": "test-request-id"
        }
    }
    
    context = MockLambdaContext()
    
    response = index.handler(event, context)
    body = json.loads(response["body"])
    
    # Verify latency is included and is a positive number
    assert "latency_ms" in body["checks"]["dynamodb"]
    latency = body["checks"]["dynamodb"]["latency_ms"]
    assert isinstance(latency, (int, float))
    assert latency >= 0


def test_health_endpoint_version_field(mock_env, dynamodb_table):
    """Test that health endpoint includes version field."""
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
        "path": "/health",
        "requestContext": {
            "requestId": "test-request-id"
        }
    }
    
    context = MockLambdaContext()
    
    response = index.handler(event, context)
    body = json.loads(response["body"])
    
    assert "version" in body
    assert body["version"] == "1.0.0"


def test_health_endpoint_timestamp_format(mock_env, dynamodb_table):
    """Test that health endpoint timestamp is in ISO8601 format."""
    import sys
    import importlib
    from datetime import datetime
    
    lambda_path = "/projects/sandbox/serverless-patterns/apigw-http-api-lambda-dynamodb-python-cdk/lambda/apigw-handler"
    if lambda_path not in sys.path:
        sys.path.insert(0, lambda_path)
    
    import index
    if 'index' in sys.modules:
        importlib.reload(index)
    
    event = {
        "httpMethod": "GET",
        "path": "/health",
        "requestContext": {
            "requestId": "test-request-id"
        }
    }
    
    context = MockLambdaContext()
    
    response = index.handler(event, context)
    body = json.loads(response["body"])
    
    # Verify timestamp can be parsed as ISO8601
    timestamp = body["timestamp"]
    try:
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
    except ValueError:
        pytest.fail(f"Timestamp {timestamp} is not in valid ISO8601 format")
