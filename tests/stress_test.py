import requests
import time
import json
import concurrent.futures

BASE_URL = "http://localhost:8000"
HEADERS = {"X-User-Role": "doctor", "X-User-Id": "DOC-001"}

print("=== 1. NLP EXTRACTION ACCURACY TEST ===")
nlp_tests = [
    "Patient started taking 500mg Metformin today.",
    "Started Aspirin 81mg on 2024-01-15, stopped on 2024-06-15.",
    "The patient was prescribed Lisinopril yesterday."
]

for text in nlp_tests:
    start_time = time.time()
    try:
        res = requests.post(f"{BASE_URL}/api/medications/nlp", headers=HEADERS, json={"patient_id": "PT-1001", "query": text})
        duration = time.time() - start_time
        print(f"Input: {text}")
        print(f"Response ({duration:.2f}s): {json.dumps(res.json(), indent=2)}\n")
    except Exception as e:
        print(f"Failed to connect: {e}")

print("=== 2. RAG CHATBOT ACCURACY TEST ===")
chat_tests = [
    "What was the highest recorded Total Cholesterol?",
    "List all dates when HbA1c was measured.",
    "Is the patient healthy? Are they doing better?" # Constraint test
]

for q in chat_tests:
    start_time = time.time()
    try:
        res = requests.post(f"{BASE_URL}/api/chat", headers=HEADERS, json={"patient_id": "PT-1001", "question": q, "history": []})
        duration = time.time() - start_time
        print(f"Question: {q}")
        print(f"Response ({duration:.2f}s): {res.json().get('answer', '')}\n")
    except Exception as e:
        print(f"Failed to connect: {e}")

print("=== 3. DB READ STRESS TEST (LocalStack + FastAPI) ===")
def fetch_records():
    try:
        res = requests.get(f"{BASE_URL}/api/records/PT-1001", headers=HEADERS)
        return res.status_code
    except:
        return 500

start_time = time.time()
num_requests = 100
successes = 0

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(lambda _: fetch_records(), range(num_requests)))
    
for r in results:
    if r == 200:
        successes += 1

duration = time.time() - start_time
print(f"Executed {num_requests} concurrent requests to DB endpoint.")
print(f"Success Rate: {successes}/{num_requests} ({(successes/num_requests)*100}%)")
print(f"Total Time: {duration:.2f}s")
print(f"Requests per second: {num_requests/duration:.2f} req/s")
