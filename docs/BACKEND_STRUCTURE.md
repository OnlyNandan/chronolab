# Backend Structure

## Data Layer (DynamoDB)
- **Table Name:** `chronolab-records`
- **Partition Key:** `patient_id` (String)
- **Sort Key:** `date` (String, YYYY-MM-DD format)
- **Fields:**
  - `field_name` (String): e.g., "HbA1c", "Fasting Glucose", "Total Cholesterol"
  - `value` (Number/Decimal)
  - `unit` (String)
  - `s3_key` (String): Reference to the original PDF report.

## Storage Layer (S3)
- **Bucket Name:** `chronolab-reports`
- **Objects:** Raw PDF lab reports uploaded for processing.

## Server (FastAPI)
- **File:** `backend/server.py`
- **Port:** 8000
- **Routes:**
  - `GET /api/data?patient_id={id}`: Queries DynamoDB for the specified patient and returns a JSON array of their canonicalized lab records.

## Pipelines
- **File:** `backend/pipeline.py`
- **Phase A (Raw Extraction):** Uses Ollama (`llava:7b` / `qwen2.5:3b`) to extract raw text and metrics from PDFs.
- **Phase B (Canonicalization):** Uses Ollama (`qwen2.5:3b`) to map raw extractions to the standard schema (`field_name`, `value`, `unit`), converting units where necessary.
- **Integration:** `backend/demo_script.py` ties the fixture generation, S3 upload, Pipeline processing, and DynamoDB storage together end-to-end.

## Agent Architecture
- **File:** `backend/doctor_mode.py`
- **Role:** "New Doctor Mode" agent.
- **Rules:** Reads JSON history from DynamoDB. Strictly prohibited from outputting diagnostic text, treatment advice, or qualitative judgments. Outputs purely factual mathematical trend changes.
