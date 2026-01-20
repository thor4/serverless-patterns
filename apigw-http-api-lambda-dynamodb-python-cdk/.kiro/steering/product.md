# Product Overview

AWS Serverless Pattern sample demonstrating API Gateway → Lambda → DynamoDB integration.

## Purpose
Reference implementation showing how to deploy a Lambda function inside a VPC that:
- Receives HTTP requests via API Gateway REST API
- Writes data to DynamoDB through a VPC endpoint
- Demonstrates secure, isolated network architecture

## Key Features
- VPC-isolated Lambda function
- DynamoDB VPC Gateway Endpoint for private connectivity
- REST API with Lambda proxy integration
- Infrastructure as Code using AWS CDK

## Use Case
Insert records into DynamoDB via HTTP POST requests with JSON payload containing `year`, `title`, and `id` fields.
