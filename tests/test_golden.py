import os
import pytest
from dotenv import load_dotenv

load_dotenv()

from domain.schemas import TicketTriage, TicketCategory, SeverityLevel, SentimentAnalysis
from domain.extraction_service import ExtractionService
from infrastructure.openai_compatible_client import OpenAICompatibleClient

API_KEY = os.getenv("API_KEY", "")
BASE_URL = os.getenv("BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

if not API_KEY:
    pytest.skip("Skipping golden tests: API_KEY is not set.", allow_module_level=True)

client = OpenAICompatibleClient(api_key=API_KEY, base_url=BASE_URL, model_name=MODEL_NAME)
service = ExtractionService(llm_client=client)

SYSTEM_PROMPT = (
    "You are an expert customer operations triage agent. Analyze the provided customer ticket "
    "and extract structural metadata representing category, severity, sentiment, and summary. "
    "Strictly follow your instructions and output schemas."
)

GOLDEN_TESTS = [
    {
        "id": "01_clear_bug_happy_path",
        "ticket": (
            "Whenever I try to click the checkout button, the application crashes with a "
            "NullPointerException error. Please fix this immediately, I am unable to buy my products."
        ),
        "expected_category": TicketCategory.BUG,
        "expected_severity": SeverityLevel.HIGH,
    },
    {
        "id": "02_ambiguous_billing_bug_intersection",
        "ticket": (
            "I was double charged on my invoice #9012 for the custom plan, "
            "but also my database synchronization is throwing API timeout warnings since yesterday. "
            "Need help on both."
        ),
        "expected_category": TicketCategory.BILLING,
        "expected_severity": SeverityLevel.HIGH,
    },
    {
        "id": "03_critical_outage_summary_length_rule",
        "ticket": (
            "My entire production cluster has dropped offline! None of our users can access our "
            "applications, and we are losing thousands of dollars every single minute. "
            "Get an on-call engineer here now!"
        ),
        "expected_category": TicketCategory.BUG,
        "expected_severity": SeverityLevel.CRITICAL,
    },
    {
        "id": "04_feature_request_low_severity",
        "ticket": (
            "It would be amazing if your platform offered a dark-theme option for the administrative "
            "control dashboards. Our night-shift monitoring operations team would highly appreciate it."
        ),
        "expected_category": TicketCategory.FEATURE_REQUEST,
        "expected_severity": SeverityLevel.LOW,
    },
    {
        "id": "05_account_access_medium_severity",
        "ticket": (
            "I forgot my password and cannot sign in to my account. "
            "I tried resetting it but I didn't receive the email link."
        ),
        "expected_category": TicketCategory.ACCOUNT,
        "expected_severity": SeverityLevel.MEDIUM,
    },
    {
        "id": "06_general_compliance_inquiry",
        "ticket": (
            "Could you provide information regarding your compliance standards? "
            "Specifically, do you maintain active SOC2 Type II certifications?"
        ),
        "expected_category": TicketCategory.OTHER,
        "expected_severity": SeverityLevel.LOW,
    },
    {
        "id": "07_sentiment_severity_contradiction_trap",
        "ticket": (
            "I absolutely love your platform, thank you for all the amazing service! "
            "However, our main payment system is totally broken right now and we are completely "
            "down and bleeding revenue. This is a massive disaster but I know you guys are the "
            "best and will fix it fast!"
        ),
        "expected_category": TicketCategory.BUG,
        "expected_severity": SeverityLevel.CRITICAL,
    },
    {
        "id": "08_subtle_indirect_escalation",
        "ticket": (
            "Hey team, just noticed some lag on the user dashboards. "
            "It's not a major issue yet, but it's taking a few more seconds to load queries "
            "than it did yesterday."
        ),
        "expected_category": TicketCategory.BUG,
        "expected_severity": SeverityLevel.LOW,
    },
]

@pytest.mark.asyncio
@pytest.mark.parametrize("test_case", GOLDEN_TESTS, ids=[t["id"] for t in GOLDEN_TESTS])
async def test_golden_regression_suite(test_case: dict):
    print(f"\n{'='*60}")
    print(f"CASE: {test_case['id']}")
    print(f"TICKET: {test_case['ticket'][:80]}...")
    print(f"{'='*60}")

    result: TicketTriage = await service.extract_with_repair(
        schema=TicketTriage,
        system=SYSTEM_PROMPT,
        user_content=test_case["ticket"]
    )

    assert isinstance(result.category,  TicketCategory)
    assert isinstance(result.severity,  SeverityLevel)
    assert isinstance(result.sentiment, SentimentAnalysis)
    assert len(result.summary.strip()) > 0

    if result.severity == SeverityLevel.CRITICAL:
        assert len(result.summary.strip()) >= 25
        assert result.sentiment != SentimentAnalysis.POSITIVE

    assert result.category == test_case["expected_category"]
    assert result.severity == test_case["expected_severity"]

    print(
        f"\n✓ PASS  category={result.category.value}  "
        f"severity={result.severity.value}  "
        f"sentiment={result.sentiment.value}\n"
        f"  summary={result.summary!r}"
    )