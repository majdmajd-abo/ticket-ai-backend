![tests](https://github.com/majdmajd-abo/ticket-ai-backend/actions/workflows/tests.yml/badge.svg?branch=master)


# Ticket AI Triage API (FastAPI)

Backend service that receives a support ticket and returns a structured AI analysis:
category, urgency, sentiment, language, summary, suggested reply, tags, confidence.

## Features
- FastAPI + Pydantic schemas (stable API contract)
- OpenAI-powered analysis (JSON-only, schema validated)
- API Key auth via `X-API-Key`
- Rate limiting (30/minute)
- Request logging + `X-Request-ID`
- Tests with mocked AI (no OpenAI calls in CI)

## Run locally

### 1) Create venv + install
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install fastapi "uvicorn[standard]" python-dotenv pydantic-settings openai slowapi pytest httpx

