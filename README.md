SentinelTriage 🛡️

SentinelTriage is a highly resilient, production-grade LLM structured data extraction engine. Built to scale to millions of monthly requests, it implements defensive engineering patterns around stochastic AI components to guarantee downstream reliability.

🏛️ Architectural Philosophy

In high-throughput systems, treating an LLM as a simple deterministic function is a critical anti-pattern. SentinelTriage separates infrastructure transport, protocol state, and semantic domain business logic using Hexagonal Architecture (Ports and Adapters).

                    ┌────────────────────────┐
                    │     HTTP Clients       │
                    └───────────┬────────────┘
                                │ JSON
                                ▼
         ┌──────────────────────────────────────────────┐
         │              app/main.py (FastAPI)           │
         └──────────────────────┬───────────────────────┘
                                │
                                ▼
         ┌──────────────────────────────────────────────┐
         │   domain/extraction_service.py               │
         │   (Semantic State Machine & Repair Loop)     │
         └───────────┬──────────────────────┬───────────┘
                     │                      │
                     ▼                      ▼
  ┌──────────────────────────┐    ┌──────────────────────────┐
  │   domain/schemas.py      │    │  infrastructure/ports    │
  │   (Pydantic V2 Domain)   │    │  (StructuredLLMClient)   │
  └──────────────────────────┘    └──────────┬───────────────┘
                                             │
                                             ▼
                                  ┌──────────────────────────┐
                                  │  infrastructure/adapters │
                                  │  (OpenAICompatible)      │
                                  └──────────┬───────────────┘
                                             │ HTTP
                                             ▼
                                  ┌──────────────────────────┐
                                  │   Upstream LLM Gateway   │
                                  └──────────────────────────┘


Key Engineering Features

The Fail-Fast Principle: Enforces cross-field constraints on extracted data (e.g., forbidding critical incidents with positive sentiments or low-quality descriptions) before payloads reach critical downstream databases.

Deterministic Protocol Inspection: Validates low-level server-sent finish metadata (like finish_reason == "length" for truncation or refusal payloads) prior to parsing JSON strings.

The Semantic Feedback Loop: When business-rule validation fails, the exact Python exception context is serialized and piped back to the LLM as structured debugging instructions, enabling dynamic corrective runs.

Decoupled Gateway Abstraction: All SDK actions run behind a vendor-agnostic interface, allowing developers to migrate from OpenAI to self-hosted vLLM platforms, Groq, or xAI with a simple config hot-swap.

📂 Repository Layout

sentinel-triage/
├── .github/
│   └── workflows/
│       └── ci.yml                  # Rigorous Github Actions Pipeline
├── app/
│   ├── __init__.py
│   └── main.py                     # FastAPI Boundary and JSON Logger Setup
├── domain/
│   ├── __init__.py
│   ├── extraction_service.py       # Self-Repair State Machine
│   └── schemas.py                  # Pydantic V2 Domain & Business Validators
├── infrastructure/
│   ├── __init__.py
│   ├── abstract_client.py          # Abstract Port Contract (StructuredLLMClient)
│   └── openai_compatible_client.py # Adaptable API Adapter Implementation
├── tests/
│   ├── __init__.py
│   └── test_golden.py              # Regression Suite & Boundary Edge Cases
├── .env.example                    # Sandbox Safe Environment Blueprint
├── .gitignore
├── pyproject.toml                  # Modern PEP 621 Dependency Specification
└── README.md


🛠️ Quickstart

1. Requirements & Setup

This project uses modern Python standards. We recommend using uv for speed:

# Clone the repository
git clone [https://github.com/yourusername/sentinel-triage.git](https://github.com/yourusername/sentinel-triage.git)
cd sentinel-triage

# Sync dependencies and configure virtual environment
uv sync


2. Configure Environment

Copy .env.example to .env and set your preferred provider settings:

API_KEY=gsk_...
BASE_URL=[https://api.groq.com/openai/v1](https://api.groq.com/openai/v1)
MODEL_NAME=llama-3.3-70b-specdec


3. Launching the Service

Run the FastAPI web application:

uv run uvicorn app.main:app --reload


Visit http://localhost:8000/docs to interact with the Swagger interface.

🧪 Regression Testing (The Golden Test Set)

We maintain a rigorous regression test suite of complex support tickets, validating critical failures, boundary limits, and cognitive contradictions.

To run the full suite:

uv run pytest tests/test_golden.py -v -s


🛡️ License

Distributed under the MIT License.