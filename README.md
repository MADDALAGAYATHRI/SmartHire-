# SmartHire (Local, no AWS)

MVP implementation matching the SRS: React frontend + FastAPI backend + MongoDB + FAISS.
Docker-based local setup only.

## Quickstart (Docker)
1) Copy `.env.example` to `.env` (optional; defaults are fine)
2) `docker compose -f docker/docker-compose.yml up --build`
3) Open frontend at http://localhost:5173, API at http://localhost:8000/docs

## Features implemented
- Job creation
- Bulk resume upload (PDF or TXT). PDF text extracted via pdfminer.
- Resume scoring (TF-IDF overlap + keyword boost) and FAISS similarity search
- Candidate table with sorting/filters
- Email generator + sentiment (very simple heuristic) with logs
- Config panel to set weights
- Export CSV from dashboard

> LLM/RAG are stubbed; replace `agents/*` logic with real APIs later.
