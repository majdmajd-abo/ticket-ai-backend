from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, constr, confloat


class CustomerTier(str, Enum):
    free = "free"
    pro = "pro"
    enterprise = "enterprise"


class Channel(str, Enum):
    email = "email"
    chat = "chat"
    web = "web"
    phone = "phone"


class Category(str, Enum):
    billing = "billing"
    bug = "bug"
    feature_request = "feature_request"
    account_access = "account_access"
    performance = "performance"
    security = "security"
    integration = "integration"
    other = "other"


class Urgency(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Sentiment(str, Enum):
    negative = "negative"
    neutral = "neutral"
    positive = "positive"


class Language(str, Enum):
    en = "en"
    he = "he"
    ar = "ar"
    other = "other"


class TicketInput(BaseModel):
    subject: constr(min_length=3, max_length=120)
    message: constr(min_length=10, max_length=5000)
    customer_tier: Optional[CustomerTier] = None
    channel: Optional[Channel] = None


class TicketAnalysis(BaseModel):
    category: Category
    urgency: Urgency
    sentiment: Sentiment
    language: Language
    summary: str = Field(min_length=1, max_length=300)
    suggested_reply: str = Field(min_length=1, max_length=2000)
    tags: List[str] = Field(default_factory=list, max_length=20)
    confidence: confloat(ge=0.0, le=1.0)
