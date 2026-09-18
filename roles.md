# ChronoLab Roles & Responsibilities

In adherence to the **Doc-First AI Coding System**, the following roles are established for this repository. 

> [!IMPORTANT]
> **EVERYONE** (Human or Agent) must log their progress in `progress.txt` at the end of their workflow.

## 1. Human Developer (Nithin)
- **Role:** Product Owner & Final Reviewer.
- **Responsibilities:** 
  - Define product requirements (`docs/PRD.md`).
  - Provide final approval for implementation plans.
  - Test the full application on local hardware.
  - Update `progress.txt` when manually completing tasks or testing.

## 2. Lead AI Architect Agent
- **Role:** System Design & Planning.
- **Responsibilities:**
  - Reads `docs/` and proposes the `IMPLEMENTATION_PLAN.md` before execution.
  - Ensures the architecture strictly follows `docs/TECH_STACK.md` (e.g., enforces LocalStack over real AWS, Ollama over cloud LLMs).
  - Updates `progress.txt` when shifting from IN PROGRESS to NEXT.

## 3. Frontend AI Agent
- **Role:** UI/UX Developer.
- **Responsibilities:**
  - Strictly follows `docs/FRONTEND_GUIDELINES.md` (Premium UI, Recharts, Vanilla CSS).
  - Rejects Tailwind CSS unless explicitly overridden by the Human Developer.
  - Must update `progress.txt` when UI features are COMPLETED.

## 4. Backend AI Agent
- **Role:** Python API, Database & AI Pipeline Developer.
- **Responsibilities:**
  - Implements the Ollama-based AI pipeline (`backend/pipeline.py`).
  - Writes the FastAPI server logic and DynamoDB queries (`backend/server.py`).
  - Strictly follows `docs/BACKEND_STRUCTURE.md`.
  - Must update `progress.txt` when backend endpoints or pipeline features are COMPLETED.

## 5. Review & Debug AI Agent (Codex)
- **Role:** QA & Finalization.
- **Responsibilities:**
  - Traces cross-file root causes when errors occur.
  - Notes persistent issues in `lessons.md`.
  - Moves items from KNOWN BUGS to COMPLETED in `progress.txt` once resolved.
