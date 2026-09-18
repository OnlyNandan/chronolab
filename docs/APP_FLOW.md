# Application Flow

## 1. Mock Data Generation
- **Trigger:** Running `data/generate_fixtures.py`.
- **Action:** Generates synthetic PDF lab reports containing mock patient medical test results (e.g., HbA1c, Fasting Glucose, Total Cholesterol) for distinct patients (e.g., PT-1001, PT-1002).

## 2. Extraction Pipeline (Backend)
- **Trigger:** Running `backend/demo_script.py`.
- **Action Sequence:**
  1. **Upload:** PDF files are uploaded to an S3 bucket (hosted locally via LocalStack/Moto).
  2. **Phase A (Raw Extraction):** The script attempts to use `llava:7b` (Vision model). If unavailable, it falls back to text extraction using `qwen2.5:3b` to grab raw values.
  3. **Phase B (Canonicalization):** Raw values are pushed through another strict LLM pass (`qwen2.5:3b`) to canonicalize units and conform to standard schema fields.
  4. **Storage:** The canonicalized JSON payload is saved to the DynamoDB `chronolab-records` table.

## 3. Frontend Visualization
- **Trigger:** User opens the React application (`http://localhost:5173`).
- **Action Sequence:**
  1. The Vite app connects to the FastAPI server on `http://localhost:8000/api/data` to fetch patient records.
  2. The frontend processes the historical data into an interactive timeline using Recharts.
  3. Premium CSS styles (glassmorphism, smooth gradients) render the health timeline dynamically.

## 4. Doctor Mode Agent (Backend)
- **Trigger:** Running `backend/doctor_mode.py <patient_id>`.
- **Action Sequence:**
  1. Connects to DynamoDB and extracts the full JSON history for the patient.
  2. Feeds JSON to `qwen2.5:3b` with strict guardrails (no diagnostics, no "good/bad" phrasing).
  3. Outputs purely mathematical/descriptive trend statements.
