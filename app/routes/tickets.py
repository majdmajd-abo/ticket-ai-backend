from fastapi import APIRouter
from app.schemas import TicketInput, TicketAnalysis

router = APIRouter()


@router.post("/analyze", response_model=TicketAnalysis)
def analyze_ticket(ticket: TicketInput):
    return {
        "urgency": "high",
        "sentiment": "negative",
        "confidence_score": 0.92,
        "summary": "Customer reports a critical issue"
    }
