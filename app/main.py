import os
import time
import uuid
import logging
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Header
from starlette.requests import Request
from starlette.responses import Response

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.schemas import TicketInput, TicketAnalysis
from app.ai import analyze_ticket_with_ai

load_dotenv()

# ---- Logging ----
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger("ticket-ai-api")

app = FastAPI(title="Ticket AI Triage API", version="0.5.0")

# ---- Config ----
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
SERVICE_API_KEY = os.getenv("SERVICE_API_KEY")

# ---- Rate limiting ----
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    start = time.perf_counter()

    # request id: accept from client or generate
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id

    try:
        response: Response = await call_next(request)
    except Exception:
        # still log latency + request_id
        latency_ms = (time.perf_counter() - start) * 1000
        logger.exception(
            "request_failed request_id=%s method=%s path=%s latency_ms=%.2f",
            request_id,
            request.method,
            request.url.path,
            latency_ms,
        )
        raise

    latency_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "request_done request_id=%s method=%s path=%s status=%s latency_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        latency_ms,
    )

    # return request id to client
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health")
def health():
    return {"status": "ok"}


def require_api_key(x_api_key: Optional[str]) -> None:
    if not SERVICE_API_KEY:
        raise HTTPException(status_code=500, detail="Server misconfigured: missing SERVICE_API_KEY")
    if not x_api_key or x_api_key != SERVICE_API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.post("/analyze", response_model=TicketAnalysis)
@limiter.limit("30/minute")
def analyze(
    request: Request,
    ticket: TicketInput,
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
) -> TicketAnalysis:
    require_api_key(x_api_key)

    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(status_code=500, detail="Server misconfigured: missing OpenAI API key")

    try:
        result = analyze_ticket_with_ai(
            subject=ticket.subject,
            message=ticket.message,
            model=MODEL,
        )
        return result
    except Exception:
        # we can log with request id without leaking the ticket text
        logger.exception("ai_failed request_id=%s", getattr(request.state, "request_id", "unknown"))
        raise HTTPException(status_code=502, detail="AI analysis failed")

