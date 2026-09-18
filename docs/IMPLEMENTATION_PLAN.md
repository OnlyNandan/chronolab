# Implementation Plan

This tracks the overarching build sequence of ChronoLab as dictated by the First Commit instructions.

## 1. Phase P0 (COMPLETED)
- [x] **1.1 Setup Infra:** Start LocalStack (`moto_server`) for S3 and DynamoDB.
- [x] **1.2 Generate Data:** Write `data/generate_fixtures.py` for synthetic PDF lab reports.
- [x] **1.3 Backend Pipeline:** Implement `backend/pipeline.py` (Phase A Vision/Text and Phase B Canonicalization).
- [x] **1.4 Demo Script:** Write `backend/demo_script.py` for end-to-end upload and processing.
- [x] **1.5 API Layer:** Build `backend/server.py` (FastAPI) to serve records.
- [x] **1.6 Frontend UI:** Build `frontend/src/Timeline.jsx` with premium CSS and Recharts.

## 2. Phase P1 (COMPLETED)
- [x] **2.1 Doctor Mode Agent:** Implement `backend/doctor_mode.py`. Connect to DynamoDB, fetch JSON history, and use an Ollama agent to output descriptive trend statements. Enforce strict guardrails against diagnostic conclusions and qualitative terms.

## 3. Phase P2 (PENDING)
- [ ] **3.1 Cedar Auth:** Implement minimal Cedar policy via LocalStack for RBAC configuration.
- [ ] **3.2 Frontend Query/CRUD:** Build a Medications CRUD form or an NLP query box on the React UI.
