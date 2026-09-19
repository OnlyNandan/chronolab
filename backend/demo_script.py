import os
import glob
import uuid
import json
from pipeline import run_pipeline
from config import get_boto3_client, get_dynamodb_table, get_s3_bucket_name

s3 = get_boto3_client('s3')
table = get_dynamodb_table()

def upload_to_s3(pdf_path, filename):
    print(f"Uploading {filename} to S3...")
    with open(pdf_path, "rb") as f:
        s3.put_object(Bucket=get_s3_bucket_name(), Key=filename, Body=f)

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
