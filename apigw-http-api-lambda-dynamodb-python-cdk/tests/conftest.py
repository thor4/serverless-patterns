# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""
Pytest configuration and shared fixtures.
"""

import os
import sys
import pytest

# Add the lambda handler to the Python path for imports
lambda_path = os.path.join(os.path.dirname(__file__), '..', 'lambda', 'apigw-handler')
if lambda_path not in sys.path:
    sys.path.insert(0, lambda_path)


# Configure Powertools for testing
os.environ['POWERTOOLS_TRACE_DISABLED'] = '1'
os.environ['POWERTOOLS_METRICS_NAMESPACE'] = 'ServerlessApp'
os.environ['POWERTOOLS_SERVICE_NAME'] = 'serverless-api'


@pytest.fixture(autouse=True)
def reset_powertools():
    """Reset Powertools state between tests."""
    # This ensures each test starts fresh
    yield
    # Cleanup after test
