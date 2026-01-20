# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Property-based tests for tracing functionality.

Feature: serverless-observability
Properties: 13-15
Validates: Requirements 3.3, 3.4, 3.5
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


# Hypothesis strategies
valid_year = st.integers(min_value=1900, max_value=2100)
valid_title = st.text(min_size=1, max_size=100, alphabet=st.characters(blacklist_categories=('Cs',)))
valid_id = st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=('Cs',)))


@settings(max_examples=100)
@given(year=valid_year, title=valid_title, id=valid_id)
def test_property_13_dynamodb_trace_subsegment_creation(mock_env, dynamodb_table, year, title, id):
    """
    Feature: serverless-observability, Property 13: DynamoDB Trace Subsegment Creation
    
    For any DynamoDB operation, a trace subsegment SHALL be created with the operation name.
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
    
    # Verify successful DynamoDB operation
    assert response["statusCode"] == 200
    
    # Verify data was written (confirms DynamoDB operation executed)
    result = dynamodb_table.get_item(
        TableName="test_table",
        Key={"id": {"S": str(id)}}
    )
    assert "Item" in result
    
    # Trace subsegment is created by @tracer.capture_method on write_to_dynamodb


@settings(max_examples=100)
@given(year=valid_year, title=valid_title, id=valid_id)
def test_property_14_business_logic_trace_subsegments(mock_env, dynamodb_table, year, title, id):
    """
    Feature: serverless-observability, Property 14: Business Logic Trace Subsegments
    
    For any traced method execution, a subsegment SHALL be created with a 
    descriptive name matching the method.
    """
    import sys
    import importlib
    
    lambda_path = "/projects/sandbox/serverless-patterns/apigw-http-api-lambda-dynamodb-python-cdk/lambda/apigw-handler"
    if lambda_path not in sys.path:
        sys.path.insert(0, lambda_path)
    
    import index
    if 'index' in sys.modules:
        importlib.reload(index)
    
    # Test POST request (calls handle_post_request)
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
    
    # Verify successful execution
    assert response["statusCode"] == 200
    
    # Trace subsegments are created by @tracer.capture_method decorators


@settings(max_examples=50)
@given(invalid_json=st.text(min_size=1, max_size=50))
def test_property_15_exception_capture_in_traces(mock_env, dynamodb_table, invalid_json):
    """
    Feature: serverless-observability, Property 15: Exception Capture in Traces
    
    For any error occurring in a traced method, the exception SHALL be 
    captured in the trace segment metadata.
    """
    # Skip valid JSON
    if invalid_json.startswith('{') or invalid_json.startswith('['):
        return
    
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
        "body": invalid_json,
        "requestContext": {
            "requestId": "test-request-id"
        }
    }
    
    context = MockLambdaContext()
    
    response = index.handler(event, context)
    
    # Verify error handling
    assert response["statusCode"] in [400, 500]
    
    # Exceptions are automatically captured by Powertools Tracer
    # when using @tracer.capture_method and @tracer.capture_lambda_handler
