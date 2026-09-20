import json
from boto3.dynamodb.conditions import Key
import sys

try:
    from .config import get_dynamodb_table  # imported as backend.doctor_mode
    from . import providers
except ImportError:
    from config import get_dynamodb_table  # run standalone: python doctor_mode.py
    import providers


def fetch_patient_history(patient_id: str):
    table = get_dynamodb_table()
    response = table.query(
        KeyConditionExpression=Key('patient_id').eq(patient_id)
    )
    # Convert Decimals to float for JSON serialization
    from decimal import Decimal
    class DecimalEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, Decimal):
                return float(obj)
            return super(DecimalEncoder, self).default(obj)
            
    items = response.get('Items', [])
    return json.dumps(items, cls=DecimalEncoder, indent=2)

def generate_doctor_summary(patient_history_json: str):
    system_prompt = """
    You are the 'New Doctor Mode' agent for ChronoLab. Your ONLY job is to output descriptive trend statements based on the provided patient history.
    
    CRITICAL AND UNBREAKABLE RULES:
    1. NEVER make diagnostic conclusions.
    2. NEVER make treatment-efficacy judgments.
    3. NEVER use qualitative words like "good", "bad", "healthy", "unhealthy", "worse", "better", "improvement", "worsening", "significant", "normal", or "abnormal".
    4. ONLY output factual, mathematical trend statements (e.g., "HbA1c increased from 6.0% to 7.5% between 2024 and 2026").
    5. Do not include any greeting or conversational filler.
    
    If you violate these rules, the system will fail.
    """
    
    prompt = f"Patient History JSON:\n{patient_history_json}\n\nPlease provide the descriptive trend summary."
    
    try:
        return providers.get_provider().chat(system_prompt, prompt, temperature=0.2)
    except Exception as e:
        return f"Error generating summary: {e}"

if __name__ == "__main__":
    patient_id = "PT-1002" if len(sys.argv) < 2 else sys.argv[1]
    print(f"Fetching history for {patient_id}...")
    history_json = fetch_patient_history(patient_id)
    
    if len(json.loads(history_json)) == 0:
        print("No records found.")
    else:
        print("Generating New Doctor Mode summary...\n")
        summary = generate_doctor_summary(history_json)
        print("--- SUMMARY ---")
        print(summary)
        print("---------------")
