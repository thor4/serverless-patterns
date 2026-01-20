# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import os
import json
import uuid
import time
from datetime import datetime
from typing import Any, Dict, Tuple, Optional

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext

# Initialize Powertools components
logger = Logger(service="serverless-api")
metrics = Metrics(namespace="ServerlessApp", service="serverless-api")
tracer = Tracer(service="serverless-api")

dynamodb_client = boto3.client("dynamodb")

APP_VERSION = "1.0.0"


@logger.inject_lambda_context(log_event=True, correlation_id_path="requestContext.requestId")
@metrics.log_metrics(capture_cold_start_metric=True)
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """Main Lambda handler with observability instrumentation."""
    start_time = time.time()
    
    try:
        # Extract HTTP method and path
        http_method = event.get("httpMethod", "")
        path = event.get("path", "/")
        
        logger.info(f"Processing {http_method} request to {path}")
        
        # Route request based on method and path
        if http_method == "GET" and path == "/health":
            response = handle_health_check()
        elif http_method == "POST" and path == "/":
            response = handle_post_request(event)
        else:
            response = {
                "statusCode": 404,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"message": "Not Found"}),
            }
            metrics.add_metric(name="ClientErrors", unit=MetricUnit.Count, value=1)
            metrics.add_dimension(name="endpoint", value=path)
            metrics.add_dimension(name="status_code", value="404")
        
        # Record request latency
        duration_ms = (time.time() - start_time) * 1000
        status_code = response.get("statusCode", 500)
        
        logger.info(f"Request completed", extra={
            "status_code": status_code,
            "duration_ms": round(duration_ms, 2)
        })
        
        # Emit metrics based on status code
        metrics.add_metric(name="RequestLatency", unit=MetricUnit.Milliseconds, value=duration_ms)
        metrics.add_dimension(name="endpoint", value=path)
        metrics.add_dimension(name="method", value=http_method)
        
        if 200 <= status_code < 300:
            metrics.add_metric(name="SuccessfulRequests", unit=MetricUnit.Count, value=1)
        elif 400 <= status_code < 500:
            metrics.add_metric(name="ClientErrors", unit=MetricUnit.Count, value=1)
            metrics.add_dimension(name="status_code", value=str(status_code))
        elif status_code >= 500:
            metrics.add_metric(name="ServerErrors", unit=MetricUnit.Count, value=1)
            metrics.add_dimension(name="status_code", value=str(status_code))
        
        return response
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.exception("Error processing request", extra={
            "duration_ms": round(duration_ms, 2)
        })
        
        # Emit error metrics
        metrics.add_metric(name="ServerErrors", unit=MetricUnit.Count, value=1)
        metrics.add_dimension(name="status_code", value="500")
        
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "message": "Internal server error",
                "correlation_id": context.aws_request_id
            }),
        }


@tracer.capture_method
def handle_post_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle POST requests to write data to DynamoDB."""
    table = os.environ.get("TABLE_NAME")
    
    logger.append_keys(table_name=table, operation="post_request")
    
    try:
        if event.get("body"):
            item = json.loads(event["body"])
            logger.info("Received payload", extra={"item": item})
            year = str(item["year"])
            title = str(item["title"])
            id = str(item["id"])
        else:
            logger.info("Received request without a payload, using defaults")
            year = "2012"
            title = "The Amazing Spider-Man 2"
            id = str(uuid.uuid4())
        
        # Write to DynamoDB with timing
        write_to_dynamodb({
            "year": year,
            "title": title,
            "id": id
        })
        
        message = "Successfully inserted data!"
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": message}),
        }
        
    except json.JSONDecodeError as e:
        logger.error("Invalid JSON in request body", extra={"error": str(e)})
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Invalid JSON in request body"}),
        }
    except KeyError as e:
        logger.error("Missing required field", extra={"field": str(e)})
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": f"Missing required field: {str(e)}"}),
        }
    except Exception as e:
        logger.exception("Error writing to DynamoDB")
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"message": "Database operation failed"}),
        }


@tracer.capture_method
def handle_health_check() -> Dict[str, Any]:
    """Handle GET /health requests."""
    logger.info("Performing health check")
    
    is_healthy, latency_ms, error_msg = check_dynamodb_health()
    
    table_name = os.environ.get("TABLE_NAME")
    timestamp = datetime.utcnow().isoformat() + "Z"
    
    if is_healthy:
        response_body = {
            "status": "healthy",
            "timestamp": timestamp,
            "checks": {
                "dynamodb": {
                    "status": "healthy",
                    "latency_ms": round(latency_ms, 2),
                    "table_name": table_name
                }
            },
            "version": APP_VERSION
        }
        status_code = 200
        logger.info("Health check passed", extra={"latency_ms": round(latency_ms, 2)})
    else:
        response_body = {
            "status": "unhealthy",
            "timestamp": timestamp,
            "checks": {
                "dynamodb": {
                    "status": "unhealthy",
                    "error": error_msg,
                    "table_name": table_name
                }
            },
            "version": APP_VERSION
        }
        status_code = 503
        logger.error("Health check failed", extra={"error": error_msg})
    
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(response_body),
    }


@tracer.capture_method
def write_to_dynamodb(item: Dict[str, str]) -> None:
    """Write item to DynamoDB with tracing."""
    table = os.environ.get("TABLE_NAME")
    start_time = time.time()
    
    logger.info("Writing to DynamoDB", extra={
        "table_name": table,
        "operation": "put_item"
    })
    
    try:
        dynamodb_client.put_item(
            TableName=table,
            Item={
                "year": {"N": item["year"]},
                "title": {"S": item["title"]},
                "id": {"S": item["id"]}
            },
        )
        
        # Record DynamoDB operation latency
        duration_ms = (time.time() - start_time) * 1000
        metrics.add_metric(name="DynamoDBLatency", unit=MetricUnit.Milliseconds, value=duration_ms)
        metrics.add_dimension(name="operation", value="put_item")
        metrics.add_dimension(name="table", value=table)
        
        tracer.put_annotation(key="table_name", value=table)
        tracer.put_annotation(key="operation", value="put_item")
        tracer.put_metadata(key="item_id", value=item["id"])
        
        logger.info("DynamoDB write successful", extra={
            "duration_ms": round(duration_ms, 2)
        })
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.exception("DynamoDB write failed", extra={
            "duration_ms": round(duration_ms, 2)
        })
        tracer.put_metadata(key="error", value=str(e))
        raise


def check_dynamodb_health() -> Tuple[bool, float, Optional[str]]:
    """Check DynamoDB connectivity and return health status."""
    table = os.environ.get("TABLE_NAME")
    start_time = time.time()
    
    try:
        dynamodb_client.describe_table(TableName=table)
        latency_ms = (time.time() - start_time) * 1000
        return True, latency_ms, None
    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000
        error_msg = str(e)
        return False, latency_ms, error_msg
