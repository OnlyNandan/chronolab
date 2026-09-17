#!/bin/bash
set -e

echo "To start LocalStack, run:"
echo "docker run -d -p 4566:4566 -p 4510-4559:4510-4559 --name localstack_main localstack/localstack"

# For this environment we will just run the boto3 setup
echo "Creating resources via boto3..."
python infra/create_resources.py
