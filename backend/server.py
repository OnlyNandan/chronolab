from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import boto3
from boto3.dynamodb.conditions import Key

app = FastAPI(title="ChronoLab API")

# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

ENDPOINT_URL = "http://localhost:4566"
REGION = "us-east-1"
AWS_ACCESS_KEY_ID = "test"
AWS_SECRET_ACCESS_KEY = "test"

dynamodb = boto3.resource(
    'dynamodb', 
    endpoint_url=ENDPOINT_URL, 
    region_name=REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

table = dynamodb.Table('chronolab-records')

@app.get("/api/records/{patient_id}")
def get_patient_records(patient_id: str):
    response = table.query(
        KeyConditionExpression=Key('patient_id').eq(patient_id)
    )
    return response.get('Items', [])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
