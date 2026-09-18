from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import boto3
from boto3.dynamodb.conditions import Key
from pydantic import BaseModel
import ollama
import json
import uuid
import datetime
from .auth_middleware import requires_auth
from .doctor_mode import fetch_patient_history, generate_doctor_summary

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

# WebSocket Manager for Real-Time Collaboration
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            await connection.send_json(message)

manager = ConnectionManager()

@app.websocket("/ws/timeline/{patient_id}")
async def websocket_endpoint(websocket: WebSocket, patient_id: str):
    await manager.connect(websocket)
    try:
        while True:
            # We just listen to keep connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/api/records/{patient_id}")
@requires_auth()
async def get_patient_records(request: Request, patient_id: str):
    response = table.query(
        KeyConditionExpression=Key('patient_id').eq(patient_id)
    )
    # Filter out medications for this endpoint (if they exist)
    items = response.get('Items', [])
    records = [item for item in items if not item.get('record_id', '').startswith('MED#')]
    return records

@app.get("/api/medications/{patient_id}")
@requires_auth()
async def get_patient_medications(request: Request, patient_id: str):
    response = table.query(
        KeyConditionExpression=Key('patient_id').eq(patient_id) & Key('record_id').begins_with('MED#')
    )
    return response.get('Items', [])

class NLPQuery(BaseModel):
    query: str
    patient_id: str

@app.post("/api/medications/nlp")
@requires_auth()
async def add_medication_nlp(request: Request, payload: NLPQuery):
    system_prompt = """
    Extract medication details from the user's natural language input.
    Output ONLY valid JSON matching this schema:
    {
      "drug_name": "string",
      "start_date": "YYYY-MM-DD",
      "end_date": "YYYY-MM-DD or null"
    }
    If the date is missing, use the current date or guess based on context.
    """
    
    try:
        response = ollama.chat(
            model='qwen2.5:3b',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': payload.query}
            ],
            format='json',
            options={'temperature': 0.1}
        )
        data = json.loads(response['message']['content'])
        
        # Save to DynamoDB
        record_id = f"MED#{datetime.datetime.now().strftime('%Y-%m-%d')}#{str(uuid.uuid4())[:8]}"
        item = {
            "patient_id": payload.patient_id,
            "record_id": record_id,
            "test_name_canonical": "Medication",
            "drug_name": data.get("drug_name"),
            "start_date": data.get("start_date"),
            "end_date": data.get("end_date")
        }
        
        table.put_item(Item=item)
        
        # Broadcast the new medication to all connected clients
        await manager.broadcast({"type": "NEW_MEDICATION", "data": item})
        
        return {"status": "success", "medication": item}
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/insights/{patient_id}")
@requires_auth()
async def get_doctor_insights(request: Request, patient_id: str):
    try:
        history_json = fetch_patient_history(patient_id)
        if len(json.loads(history_json)) == 0:
            return {"insights": "No patient records found."}
        
        summary = generate_doctor_summary(history_json)
        return {"insights": summary}
    except Exception as e:
        return {"insights": f"Error generating insights: {e}"}

@app.get("/api/export/fhir/{patient_id}")
@requires_auth()
async def export_fhir(request: Request, patient_id: str):
    response = table.query(
        KeyConditionExpression=Key('patient_id').eq(patient_id)
    )
    items = response.get('Items', [])
    
    # Mocked FHIR Bundle for Hackathon Demonstration
    bundle = {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": []
    }
    
    for item in items:
        if item.get('record_id', '').startswith('MED#'):
            entry = {
                "resource": {
                    "resourceType": "MedicationStatement",
                    "status": "active",
                    "medicationCodeableConcept": {
                        "coding": [{"display": item.get('drug_name')}]
                    },
                    "effectivePeriod": {
                        "start": item.get('start_date'),
                        "end": item.get('end_date')
                    }
                }
            }
        else:
            entry = {
                "resource": {
                    "resourceType": "Observation",
                    "status": "final",
                    "code": {
                        "coding": [{"display": item.get('test_name_canonical')}]
                    },
                    "valueQuantity": {
                        "value": float(item.get('value', 0)) if item.get('value') else 0,
                        "unit": item.get('unit', '')
                    },
                    "effectiveDateTime": item.get('date_time', '')
                }
            }
        bundle["entry"].append(entry)
        
    return JSONResponse(content=bundle)

class ChatQuery(BaseModel):
    patient_id: str
    question: str
    history: list = []

@app.post("/api/chat")
@requires_auth()
async def chat_with_timeline(request: Request, payload: ChatQuery):
    try:
        # 1. Fetch Timeline Data
        history_json = fetch_patient_history(payload.patient_id)
        
        # 2. Construct System Prompt
        system_prompt = f"""
        You are an AI Timeline Assistant for ChronoLab. Your job is to answer questions about the patient's medical timeline.
        
        CRITICAL CONSTRAINTS:
        1. NEVER make diagnostic conclusions.
        2. NEVER make treatment-efficacy judgments.
        3. NEVER use qualitative words like "good", "bad", "healthy", "unhealthy", "worse", "better".
        4. ONLY output factual, mathematical, or chronological statements based on the provided JSON data.
        
        PATIENT TIMELINE JSON:
        {history_json}
        """
        
        # 3. Construct Messages Array
        messages = [{'role': 'system', 'content': system_prompt}]
        for msg in payload.history:
            messages.append({'role': msg.get('role', 'user'), 'content': msg.get('content', '')})
            
        messages.append({'role': 'user', 'content': payload.question})
        
        # 4. Generate Response
        response = ollama.chat(
            model='qwen2.5:3b',
            messages=messages,
            options={'temperature': 0.2}
        )
        
        return {"answer": response['message']['content']}
        
    except Exception as e:
        return {"answer": f"Error querying timeline: {e}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
