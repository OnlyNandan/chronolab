# Technology Stack

This document tracks the exact technologies and frameworks used to build ChronoLab. Adhere to these rigidly to avoid hallucinations.

## Frontend
- **Framework:** React + Vite
- **Styling:** Vanilla CSS (App.css). Premium design (glassmorphism, rich aesthetics) is required. TailwindCSS is explicitly avoided unless requested.
- **Charts:** Recharts (used for timeline plotting)

## Backend
- **Language:** Python
- **API Framework:** FastAPI
- **Cloud Infrastructure Simulation:** LocalStack (using `moto_server` as Docker fallback)
- **AWS SDK:** `boto3` (for S3 and DynamoDB interactions)

## AI / Machine Learning
- **Model Engine:** Ollama (running locally on macOS, MPS accelerated)
- **Models:** 
  - `llava:7b` (Target for Phase A Vision - though environment fallback is in place).
  - `qwen2.5:3b` (Used for Phase A text fallback, Phase B canonicalization, and Doctor Mode).
- **Agents SDK:** Strands Agents SDK

## Data Layer
- **Blob Storage:** Amazon S3 (Simulated locally via `moto`)
- **Database:** Amazon DynamoDB (Simulated locally via `moto`, table: `chronolab-records`)

## Environment
- macOS (M3 Max / 36GB RAM)
- Python Virtual Environment (`venv`)
- Node Package Manager (`npm`)
