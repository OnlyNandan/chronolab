# Product Requirements Document (PRD)

## Project Overview
ChronoLab is an application built for the First Commit "Build It" track. It processes PDF lab reports via an AI pipeline (using Ollama models), stores the canonicalized data, and displays the patient's medical history on an interactive React timeline. It also includes a "Doctor Mode" agent that outputs descriptive trend statements based on the patient's history.

## Target Audience
Medical practitioners and patients looking to visualize their health records chronologically without manual data entry.

## In-Scope Features
- **P0 Tier:**
  - Mock lab report PDF generation (synthetic data).
  - Local infrastructure simulation via LocalStack (`moto_server`) for AWS S3 and DynamoDB.
  - Two-phase AI extraction pipeline (Phase A: Vision/Text Extraction, Phase B: Canonicalization & strict mathematical guardrails).
  - React/Vite frontend with an interactive timeline visualization (using Recharts).
- **P1 Tier:**
  - "New Doctor Mode" agent. A text-only Strands agent that parses patient JSON history into strictly descriptive, mathematical trend statements.
- **P2 Tier:**
  - Minimal Cedar Policy implementation for Auth/RBAC via LocalStack.
  - Medication CRUD operations and an NLP Query box on the frontend.

## Out-of-Scope Features (Explicit Non-Goals)
- Medical diagnostics. The AI must **never** interpret data to form diagnostic conclusions, make treatment-efficacy judgments, or characterize results as "good" or "bad".
- Production deployments (this is explicitly designed for a 3-minute demo video via a public repo).

## Success Criteria
- The core features (P0 and P1) run successfully and demonstrably from start to finish.
- The pipeline correctly parses, canonicalizes, and stores the PDF data.
- The frontend renders the extracted timeline accurately with a premium, dynamic UX.
- The repository, writeup, and video are demo-ready for the "Build It" hackathon judging.
