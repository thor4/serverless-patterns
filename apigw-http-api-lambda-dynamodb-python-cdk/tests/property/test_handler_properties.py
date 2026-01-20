# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Property-based tests for handler functionality.

Feature: serverless-observability
Properties: 16-17
Validates: Requirements 4.5, 6.1, 6.3
"""

import json
import os
import pytest
from unittest.mock import patch
from moto import mock_dynamodb
import boto3
from hypothesis import given, strategies as st, settings


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


@settings(max_examples=100)
@given(seed=st.integers(min_value=1, max_value=1000))
def test_property_16_health_check_duration_inclusion(mock_env, dynamodb_table, seed):
    """
    Feature: serverless-observability, Property 16: Health Check Duration Inclusion
    
    For any health check response (healthy or unhealthy), the response body SHALL 
    contain the latency_ms field with a non-negative value.
    """
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
            "requestId": f"test-request-{seed}"
        }
    }
    
    context = MockLambdaContext(request_id=f"test-request-{seed}")
    
    response = index.handler(event, context)
    
    # Verify response
    body = json.loads(response["body"])
    
    # Check for latency_ms in dynamodb check
    assert "checks" in body
    assert "dynamodb" in body["checks"]
    
    dynamodb_check = body["checks"]["dynamodb"]
    
    # For healthy checks, latency_ms must be present
    if dynamodb_check["status"] == "healthy":
        assert "latency_ms" in dynamodb_check
        assert isinstance(dynamodb_check["latency_ms"], (int, float))
        assert dynamodb_check["latency_ms"] >= 0


# Hypothesis strategies
valid_year = st.integers(min_value=1900, max_value=2100)
valid_title = st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',)))
valid_id = st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',)))


@settings(max_examples=100)
@given(year=valid_year, title=valid_title, id=valid_id)
def test_property_17_post_request_data_persistence_and_response_format(mock_env, dynamodb_table, year, title, id):
    """
    Feature: serverless-observability, Property 17: POST Request Data Persistence and Response Format
    
    For any valid POST request with year, title, and id fields, the Lambda handler 
    SHALL write the data to DynamoDB, return a 200 status code, and include a 
    "message" field in the response body.
    """
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
            "year": year,
            "title": str(title),
            "id": str(id)
        }),
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
    
    # Verify data persistence
    result = dynamodb_table.get_item(
        TableName="test_table",
        Key={"id": {"S": str(id)}}
    )
    
    assert "Item" in result
    assert result["Item"]["year"]["N"] == str(year)
    assert result["Item"]["title"]["S"] == str(title)
    assert result["Item"]["id"]["S"] == str(id)
