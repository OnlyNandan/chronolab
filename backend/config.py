"""
Single source of truth for AWS client construction and resource names.

AWS_MODE=local  -> boto3 clients point at LocalStack/moto_server with test credentials.
AWS_MODE=cloud  -> boto3 clients omit endpoint_url and rely on the default credential
                   chain (IAM role on EC2, or an AWS profile locally).

No other module in this codebase should call boto3.client(...) or boto3.resource(...)
directly. Resource names (bucket, table) are read from the environment; they are never
constructed here — scripts/bootstrap.sh is responsible for writing them into .env.
"""
import os

import boto3
from dotenv import load_dotenv

load_dotenv()

AWS_MODE = os.getenv("AWS_MODE", "local")
AWS_REGION = os.getenv("AWS_REGION", "ap-south-1")
LOCALSTACK_ENDPOINT_URL = os.getenv("LOCALSTACK_ENDPOINT_URL", "http://localhost:4566")

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME")

_LOCAL_TEST_CREDENTIALS = {
    "aws_access_key_id": "test",
    "aws_secret_access_key": "test",
}


def _require(value: str | None, var_name: str) -> str:
    if not value:
        raise RuntimeError(
            f"{var_name} is not set in .env. Run ./scripts/bootstrap.sh to generate it."
        )
    return value


def get_boto3_client(service_name: str):
    if AWS_MODE == "local":
        return boto3.client(
            service_name,
            endpoint_url=LOCALSTACK_ENDPOINT_URL,
            region_name=AWS_REGION,
            **_LOCAL_TEST_CREDENTIALS,
        )
    return boto3.client(service_name, region_name=AWS_REGION)


def get_boto3_resource(service_name: str):
    if AWS_MODE == "local":
        return boto3.resource(
            service_name,
            endpoint_url=LOCALSTACK_ENDPOINT_URL,
            region_name=AWS_REGION,
            **_LOCAL_TEST_CREDENTIALS,
        )
    return boto3.resource(service_name, region_name=AWS_REGION)


def get_dynamodb_table():
    table_name = _require(DYNAMODB_TABLE_NAME, "DYNAMODB_TABLE_NAME")
    return get_boto3_resource("dynamodb").Table(table_name)


def get_s3_bucket_name() -> str:
    return _require(S3_BUCKET_NAME, "S3_BUCKET_NAME")
