from enum import Enum
from pydantic import BaseModel, Field, model_validator

class TicketCategory(str, Enum):
    BILLING = "billing"
    BUG = "bug"
    FEATURE_REQUEST = "feature_request"
    ACCOUNT = "account"
    OTHER = "other"

class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SentimentAnalysis(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"

class TicketTriage(BaseModel):
    model_config = {"extra": "forbid"}

    category: TicketCategory = Field(
        description="The primary domain classification of the ticket contents."
    )
    severity: SeverityLevel = Field(
        description="Operational priority based on business impact."
    )
    sentiment: SentimentAnalysis = Field(
        description="The operational sentiment of the situation described."
    )
    summary: str = Field(
        description="A concise, factual, action-oriented summary of the core issue. CRITICAL incidents require at least 25 characters."
    )

    @model_validator(mode="after")
    def enforce_business_rules(self) -> "TicketTriage":
        summary_len = len(self.summary.strip())

        if self.severity == SeverityLevel.CRITICAL and summary_len < 25:
            raise ValueError(
                f"Escalation Rule Violation: CRITICAL incidents require an actionable summary "
                f"of at least 25 characters. "
                f"Current summary has {summary_len} characters: {self.summary!r}. "
                f"Write a complete sentence describing what is failing and the business impact."
            )

        if self.severity == SeverityLevel.CRITICAL and self.sentiment == SentimentAnalysis.POSITIVE:
            raise ValueError(
                "Contradiction Violation: A CRITICAL severity incident cannot have POSITIVE sentiment. "
                "Sentiment must reflect the operational reality of the situation. "
                "Re-evaluate sentiment as NEGATIVE or NEUTRAL."
            )

        return self