import os
import sys
import json
import logging
from typing import Any, Dict
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from domain.schemas import TicketTriage
from domain.extraction_service import ExtractionService
from infrastructure.openai_compatible_client import OpenAICompatibleClient
from infrastructure.abstract_client import TruncationException, RefusalException

# Load environment variables from .env file before initialization
load_dotenv()

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_payload: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "module": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_payload)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers = [handler]

logger = logging.getLogger("sentinel_triage.app")

app = FastAPI(
    title="SentinelTriage API",
    description="High-throughput, resilient customer support ticket parsing and classification engine.",
    version="0.1.0"
)

API_KEY = os.getenv("API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

if not API_KEY:
    logger.warning("BOOTSTRAP_WARNING: 'API_KEY' environment variable is empty. Calls will fail unless mocked.")

llm_client = OpenAICompatibleClient(api_key=API_KEY, base_url=BASE_URL, model_name=MODEL_NAME)
triage_service = ExtractionService(llm_client=llm_client)

class TriageRequest(BaseModel):
    ticket_text: str = Field(
        ...,
        description="The raw, unformatted text of the incoming customer support ticket.",
        min_length=10
    )

SYSTEM_PROMPT = (
    "You are a elite customer operations triage analyst. Analyze the provided customer ticket "
    "and extract structural metadata representing category, severity, sentiment, and summary. "
    "Strictly follow your instructions and output schemas."
)

@app.post(
    "/triage",
    response_model=TicketTriage,
    status_code=status.HTTP_200_OK,
    summary="Process support tickets with automated self-repair guarantees."
)
async def triage_ticket(request: TriageRequest):
    logger.info("INCOMING_TRIAGE_REQUEST: Initiating metadata extraction workflow.")

    try:
        validated_triage = await triage_service.extract_with_repair(
            schema=TicketTriage,
            system=SYSTEM_PROMPT,
            user_content=request.ticket_text
        )
        logger.info("TRIAGE_PROCESSING_SUCCESSFUL: Clean structure successfully generated and validated.")
        return validated_triage

    except (TruncationException, RefusalException) as e:
        logger.error(f"PROTOCOL_EXCEPTION_ABORT: Execution failed upstream model rules: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"API Policy or Context limit hit: {str(e)}"
        )

    except RuntimeError as e:
        logger.critical(f"REPAIR_BUDGET_EXHAUSTED_ABORT: System failed semantic self-repair loops: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Semantic Validation Failure: {str(e)}"
        )

    except Exception as e:
        logger.critical(f"FATAL_UNHANDLED_EXCEPTION: Pipeline error encountered: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="System failed processing request. Please refer to operational telemetry."
        )