# 🧬 ChronoLab

**Hackathon Submission for "First Commit" (Build It Track - AWS HealthTech)**

ChronoLab is a next-generation, AI-driven unified timeline for patient lab reports. Built to transcend standard dashboards, ChronoLab ingests unstructured medical data, builds mathematical and chronological health timelines, and empowers doctors with an Interactive Retrieval-Augmented Generation (RAG) assistant—all while strictly enforcing non-diagnostic constraints to ensure medical safety.

---

## 🏆 Key "World-Class" Features

1. **🎙️ Voice-to-Text NLP Interoperability**  
   Doctors can use the browser's native Web Speech API to speak medication updates (e.g., *"Patient started taking 500mg Metformin today"*). An onboard Ollama AI agent (`qwen2.5:3b`) parses the unstructured voice input into strict JSON and persists it.

2. **🤖 Interactive AI Timeline Assistant (RAG Chatbot)**  
   A beautiful, glassmorphic floating chat widget allows doctors to query the timeline. By combining FastAPI with Ollama, the backend retrieves the entire patient timeline from DynamoDB, injects it into a constrained prompt, and provides mathematically accurate answers (e.g., *"When was the highest cholesterol recorded?"*). The agent is hard-coded to *never* provide diagnostic or qualitative health conclusions.

3. **⚡ Real-Time Collaboration (WebSockets)**  
   Built for "multiplayer" clinic environments, the FastAPI backend broadcasts updates via WebSockets. If a nurse updates a medication on an iPad, the timeline instantly refreshes on the doctor's desktop without a page reload.

4. **🏥 HealthTech Interoperability (FHIR Export)**  
   A dedicated endpoint translates the DynamoDB schema into an HL7 FHIR-compliant JSON bundle, allowing users to export standardized medical records with a single click.

5. **✨ Premium "Billion-Dollar" Aesthetics**  
   The UI utilizes an animated, breathing gradient mesh background combined with deep glassmorphism (frosted glass) panels, ensuring the platform feels like a mature enterprise product.

---

## 🏗️ Architecture & Tech Stack

ChronoLab is engineered for speed, security, and local execution:

- **Frontend**: React (Vite), Vanilla CSS (Glassmorphism), WebSockets, Web Speech API.
- **Backend**: FastAPI (Python), Uvicorn, WebSockets.
- **Database**: **AWS LocalStack** (DynamoDB for NoSQL patient records).
- **AI Engine**: **Ollama** (MPS accelerated on Apple Silicon) utilizing `qwen2.5:3b` for NLP Extraction and RAG orchestration.
- **Auth Simulation**: Mocked AWS Cedar integration via custom middleware to enforce strict role-based access (`X-User-Role: doctor`).

---

## 🚀 Getting Started (Local Development)

### Prerequisites
- Python 3.10+
- Node.js & npm
- Docker (for LocalStack)
- Ollama installed locally with the `qwen2.5:3b` model pulled (`ollama pull qwen2.5:3b`).

### 1. Start Local AWS (DynamoDB)
```bash
# We use moto_server to simulate AWS services locally
pip install "moto[server]"
moto_server -p 4566
```

### 2. Start the Backend (FastAPI)
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Make sure to install websockets
pip install websockets
uvicorn server:app --host 0.0.0.0 --port 8000
```

### 3. Start the Frontend (React)
```bash
cd frontend
npm install
npm run dev
```

### 4. Run Stress Tests
```bash
python tests/stress_test.py
```
*Executes a 100-request concurrent bombardment against the DB and tests the AI agents for NLP extraction accuracy and non-diagnostic constraint enforcement.*

---

## 📜 Constraints & Philosophy
ChronoLab strictly adheres to the rule: **AI should assist, never diagnose.**
The architecture ensures that the LLM only ever outputs structured data (JSON) or mathematical/chronological truths. It is explicitly forbidden from making treatment-efficacy judgments or providing qualitative labels (e.g., "healthy"). 

---
*Built with ❤️ for the First Commit Hackathon.*
