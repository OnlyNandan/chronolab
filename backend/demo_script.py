import os
import glob
import uuid
import boto3
import json
from pipeline import run_pipeline

ENDPOINT_URL = "http://localhost:4566"
REGION = "us-east-1"
AWS_ACCESS_KEY_ID = "test"
AWS_SECRET_ACCESS_KEY = "test"

s3 = boto3.client(
    's3', 
    endpoint_url=ENDPOINT_URL, 
    region_name=REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

dynamodb = boto3.resource(
    'dynamodb', 
    endpoint_url=ENDPOINT_URL, 
    region_name=REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

table = dynamodb.Table('chronolab-records')

def upload_to_s3(pdf_path, filename):
    print(f"Uploading {filename} to S3...")
    with open(pdf_path, "rb") as f:
        s3.put_object(Bucket="chronolab-pdfs", Key=filename, Body=f)

def save_to_dynamodb(records):
    print(f"Saving {len(records)} records to DynamoDB...")
    with table.batch_writer() as batch:
        for record in records:
            # We add a unique sort key for each record
            record_id = f"LAB#{record['date']}#{uuid.uuid4().hex[:8]}"
            item = {
                'patient_id': record['patient_id'],
                'record_id': record_id,
                **record
            }
            # Convert floats to string or Decimal for DynamoDB to accept it nicely
            from decimal import Decimal
            item_decimal = json.loads(json.dumps(item), parse_float=Decimal)
            batch.put_item(Item=item_decimal)

def main():
    import json
    fixtures = glob.glob(os.path.join(os.path.dirname(__file__), "../data/*.pdf"))
    if not fixtures:
        print("No fixtures found.")
        return

    print("Starting First Commit Lab Report extraction demo...")
    for pdf_path in fixtures:
        filename = os.path.basename(pdf_path)
        print(f"\n--- Processing {filename} ---")
        
        # 1. Upload original PDF
        upload_to_s3(pdf_path, filename)
        
        # 2. Run AI pipeline
        records = run_pipeline(pdf_path)
        
        # 3. Save structured JSON to DynamoDB
        if records:
            save_to_dynamodb(records)
            print("Successfully processed and saved.")
        else:
            print("Extraction failed or returned no records.")

if __name__ == "__main__":
    main()
