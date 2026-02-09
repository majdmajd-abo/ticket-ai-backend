import json
import os
from typing import Any, Dict

from openai import OpenAI
from pydantic import ValidationError

from app.schemas import TicketAnalysis


SYSTEM_PROMPT = """You are a support-ticket triage engine.
Return ONLY valid JSON that matches the provided schema and enums.
Do not add extra keys. No markdown. No commentary.

Rules:
- If uncertain, choose "other" and lower confidence.
- confidence must be between 0 and 1.
- suggested_reply must be polite, actionable, and ask for missing info.
- category mapping hints:
  - chargeback/invoice/payment/refund -> billing
  - crash/error/stack trace/exception -> bug
  - slow/latency/timeout -> performance
  - auth/login/password/2fa/access -> account_access
  - vulnerability/breach/hacked/leak -> security
"""


def _get_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY")
    return OpenAI(api_key=api_key)


def _parse_and_validate(raw: str) -> TicketAnalysis:
    data = json.loads(raw)
    return TicketAnalysis.model_validate(data)


def analyze_ticket_with_ai(subject: str, message: str, model: str) -> TicketAnalysis:
    schema_hint: Dict[str, Any] = {
        "category": "billing|bug|feature_request|account_access|performance|security|integration|other",
        "urgency": "low|medium|high",
        "sentiment": "negative|neutral|positive",
        "language": "en|he|ar|other",
        "summary": "1-2 sentences",
        "suggested_reply": "3-6 sentences",
        "tags": ["short_tag"],
        "confidence": 0.0,
    }

    user_prompt = f"""Analyze this support ticket and return JSON only.

Ticket:
subject: {subject}
message: {message}

JSON schema hint (keys and allowed enums):
{json.dumps(schema_hint, ensure_ascii=False)}
"""

    client = _get_client()

    # Attempt 1
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
    )
    raw = (resp.choices[0].message.content or "").strip()

    try:
        return _parse_and_validate(raw)
    except (json.JSONDecodeError, ValidationError):
        # Repair attempt
        repair_prompt = f"""Fix this to be VALID JSON ONLY that matches the schema. No extra keys.

Bad output:
{raw}
"""
        resp2 = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
                {"role": "user", "content": repair_prompt},
            ],
            temperature=0.0,
        )
        raw2 = (resp2.choices[0].message.content or "").strip()
        return _parse_and_validate(raw2)

