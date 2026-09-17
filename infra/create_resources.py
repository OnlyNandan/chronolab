import boto3
from botocore.exceptions import ClientError

ENDPOINT_URL = "http://localhost:4566"
REGION = "us-east-1"
# LocalStack/Moto dummy credentials
AWS_ACCESS_KEY_ID = "test"
AWS_SECRET_ACCESS_KEY = "test"

def main():
    s3 = boto3.client(
        's3', 
        endpoint_url=ENDPOINT_URL, 
        region_name=REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )
    
    dynamodb = boto3.client(
        'dynamodb', 
        endpoint_url=ENDPOINT_URL, 
        region_name=REGION,
        aws_access_key_id=AWS_ACCESS_KEY_ID,
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY
    )

    print("Creating S3 bucket: chronolab-pdfs...")
    try:
        s3.create_bucket(Bucket="chronolab-pdfs")
        print("Bucket created.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'BucketAlreadyExists' or e.response['Error']['Code'] == 'BucketAlreadyOwnedByYou':
            print("Bucket already exists.")
        else:
            print("Error creating bucket:", e)

    print("Creating DynamoDB table: chronolab-records...")
    try:
        dynamodb.create_table(
            TableName='chronolab-records',
            KeySchema=[
                {'AttributeName': 'patient_id', 'KeyType': 'HASH'},  # Partition key
                {'AttributeName': 'record_id', 'KeyType': 'RANGE'}   # Sort key
            ],
            AttributeDefinitions=[
                {'AttributeName': 'patient_id', 'AttributeType': 'S'},
                {'AttributeName': 'record_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("Table created.")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print("Table already exists.")
        else:
            print("Error creating table:", e)

if __name__ == "__main__":
    main()
