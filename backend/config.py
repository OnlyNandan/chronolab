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

# Bedrock model access may only be approved in a different region than the one
# holding S3/DynamoDB (see MIGRATION_PLAN.md Phase 0b) — kept separate on purpose.
BEDROCK_REGION = os.getenv("BEDROCK_REGION", AWS_REGION)
BEDROCK_VISION_MODEL_ID = os.getenv(
    "BEDROCK_VISION_MODEL_ID", "anthropic.claude-3-5-sonnet-20241022-v2:0"
)
BEDROCK_TEXT_MODEL_ID = os.getenv(
    "BEDROCK_TEXT_MODEL_ID", "anthropic.claude-3-5-haiku-20241022-v1:0"
)

OLLAMA_VISION_MODEL = os.getenv("OLLAMA_VISION_MODEL", "llava:7b")
OLLAMA_TEXT_MODEL = os.getenv("OLLAMA_TEXT_MODEL", "qwen2.5:3b")

S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
DYNAMODB_TABLE_NAME = os.getenv("DYNAMODB_TABLE_NAME")
AVP_POLICY_STORE_ID = os.getenv("AVP_POLICY_STORE_ID")

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


def get_boto3_client(service_name: str, region_name: str | None = None):
    region = region_name or AWS_REGION
    if AWS_MODE == "local":
        return boto3.client(
            service_name,
            endpoint_url=LOCALSTACK_ENDPOINT_URL,
            region_name=region,
            **_LOCAL_TEST_CREDENTIALS,
        )
    return boto3.client(service_name, region_name=region)


def get_real_aws_client(service_name: str, region_name: str | None = None):
    """For services with no LocalStack/moto emulation (Cognito, Verified Permissions).

    Always hits real AWS, even when AWS_MODE=local — there is no local emulation path
    for these, so the rest of the app can stay on LocalStack while auth talks to the
    real account (see MIGRATION_PLAN.md Phase 3 / hour-12 fallback).
    """
    return boto3.client(service_name, region_name=region_name or AWS_REGION)


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


def get_avp_policy_store_id() -> str:
    return _require(AVP_POLICY_STORE_ID, "AVP_POLICY_STORE_ID")
