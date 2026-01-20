# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Unit tests for CDK stack observability configuration.

Feature: serverless-observability
Tests: Requirements 3.1, 3.2, 5.1, 5.2, 5.3, 5.4
"""

import aws_cdk as cdk
from aws_cdk import assertions
from stacks.apigw_http_api_lambda_dynamodb_python_cdk_stack import ApigwHttpApiLambdaDynamodbPythonCdkStack


def test_lambda_powertools_layer_attached():
    """Test that Powertools layer is attached to Lambda function."""
    app = cdk.App()
    stack = ApigwHttpApiLambdaDynamodbPythonCdkStack(app, "test-stack")
    template = assertions.Template.from_stack(stack)
    
    # Verify Lambda function has Powertools layer
    template.has_resource_properties("AWS::Lambda::Function", {
        "Layers": assertions.Match.array_with([
            assertions.Match.string_like_regexp(".*AWSLambdaPowertoolsPythonV3.*")
        ])
    })


def test_xray_tracing_enabled_on_lambda():
    """Test that X-Ray tracing is enabled on Lambda function."""
    app = cdk.App()
    stack = ApigwHttpApiLambdaDynamodbPythonCdkStack(app, "test-stack")
    template = assertions.Template.from_stack(stack)
    
    # Verify Lambda has X-Ray tracing enabled
    template.has_resource_properties("AWS::Lambda::Function", {
        "TracingConfig": {
            "Mode": "Active"
        }
    })


def test_xray_tracing_enabled_on_api_gateway():
    """Test that X-Ray tracing is enabled on API Gateway."""
    app = cdk.App()
    stack = ApigwHttpApiLambdaDynamodbPythonCdkStack(app, "test-stack")
    template = assertions.Template.from_stack(stack)
    
    # Verify API Gateway stage has X-Ray tracing enabled
    template.has_resource_properties("AWS::ApiGateway::Stage", {
        "TracingEnabled": True
    })


def test_powertools_environment_variables_configured():
    """Test that Powertools environment variables are configured."""
    app = cdk.App()
    stack = ApigwHttpApiLambdaDynamodbPythonCdkStack(app, "test-stack")
    template = assertions.Template.from_stack(stack)
    
    # Verify environment variables are set
    template.has_resource_properties("AWS::Lambda::Function", {
        "Environment": {
            "Variables": {
                "POWERTOOLS_SERVICE_NAME": "serverless-api",
                "POWERTOOLS_METRICS_NAMESPACE": "ServerlessApp",
                "LOG_LEVEL": "INFO",
                "TABLE_NAME": assertions.Match.any_value()
            }
        }
    })


def test_health_endpoint_exists():
    """Test that /health endpoint exists in API Gateway."""
    app = cdk.App()
    stack = ApigwHttpApiLambdaDynamodbPythonCdkStack(app, "test-stack")
    template = assertions.Template.from_stack(stack)
    
    # Verify health resource exists
    template.has_resource_properties("AWS::ApiGateway::Resource", {
        "PathPart": "health"
    })
    
    # Verify GET method exists on health endpoint
    template.has_resource_properties("AWS::ApiGateway::Method", {
        "HttpMethod": "GET"
    })


def test_lambda_has_xray_permissions():
    """Test that Lambda function has X-Ray permissions."""
    app = cdk.App()
    stack = ApigwHttpApiLambdaDynamodbPythonCdkStack(app, "test-stack")
    template = assertions.Template.from_stack(stack)
    
    # When X-Ray tracing is active, CDK automatically adds these permissions
    # Verify IAM role has policy for X-Ray
    template.has_resource_properties("AWS::IAM::Policy", {
        "PolicyDocument": {
            "Statement": assertions.Match.array_with([
                assertions.Match.object_like({
                    "Action": assertions.Match.array_with([
                        "xray:PutTraceSegments",
                        "xray:PutTelemetryRecords"
                    ]),
                    "Effect": "Allow"
                })
            ])
        }
    })


def test_lambda_has_dynamodb_permissions():
    """Test that Lambda has DynamoDB write and describe permissions."""
    app = cdk.App()
    stack = ApigwHttpApiLambdaDynamodbPythonCdkStack(app, "test-stack")
    template = assertions.Template.from_stack(stack)
    
    # Verify Lambda has DynamoDB permissions
    template.has_resource_properties("AWS::IAM::Policy", {
        "PolicyDocument": {
            "Statement": assertions.Match.array_with([
                assertions.Match.object_like({
                    "Action": assertions.Match.array_with([
                        "dynamodb:PutItem",
                        "dynamodb:DescribeTable"
                    ]),
                    "Effect": "Allow"
                })
            ])
        }
    })


def test_lambda_runtime_version():
    """Test that Lambda uses Python 3.10 runtime."""
    app = cdk.App()
    stack = ApigwHttpApiLambdaDynamodbPythonCdkStack(app, "test-stack")
    template = assertions.Template.from_stack(stack)
    
    # Verify Lambda runtime
    template.has_resource_properties("AWS::Lambda::Function", {
        "Runtime": "python3.10"
    })


def test_vpc_configuration():
    """Test that Lambda is deployed in VPC with isolated subnets."""
    app = cdk.App()
    stack = ApigwHttpApiLambdaDynamodbPythonCdkStack(app, "test-stack")
    template = assertions.Template.from_stack(stack)
    
    # Verify Lambda has VPC configuration
    template.has_resource_properties("AWS::Lambda::Function", {
        "VpcConfig": {
            "SubnetIds": assertions.Match.any_value(),
            "SecurityGroupIds": assertions.Match.any_value()
        }
    })


def test_dynamodb_table_created():
    """Test that DynamoDB table is created with correct configuration."""
    app = cdk.App()
    stack = ApigwHttpApiLambdaDynamodbPythonCdkStack(app, "test-stack")
    template = assertions.Template.from_stack(stack)
    
    # Verify DynamoDB table
    template.has_resource_properties("AWS::DynamoDB::Table", {
        "KeySchema": [
            {
                "AttributeName": "id",
                "KeyType": "HASH"
            }
        ]
    })
