import logging
from typing import Type, TypeVar
from pydantic import BaseModel, ValidationError
from infrastructure.abstract_client import TruncationException, RefusalException

logger = logging.getLogger("sentinel_triage.domain.service")
T = TypeVar("T", bound=BaseModel)


class RepairBudgetExhaustedError(Exception):
    """Raised when the semantic repair loop cannot satisfy the schema."""

class ExtractionService:
    """
    Domain orchestrator service coordinating extraction and semantic self-repair loops.
    """

    def __init__(self, llm_client):
        self.llm_client = llm_client

    async def extract_with_repair(
        self,
        schema: Type[T],
        system: str,
        user_content: str,
        max_retries: int = 2
    ) -> T:
        current_content = user_content
        last_error = None

        for attempt in range(max_retries + 1):
            try:
                logger.info(f"SEMANTIC_ATTEMPT: Processing extraction attempt {attempt + 1}/{max_retries + 1}")

                raw_dict = await self.llm_client.raw_extract(
                    schema=schema,
                    system_instruction=system,
                    user_content=current_content
                )

                validated_model = schema.model_validate(raw_dict)

                if attempt > 0:
                    logger.info("SEMANTIC_REPAIR_SUCCESS: Model corrected its previous validation mistake.")

                return validated_model

            except ValidationError as e:
                last_error = e
                logger.warning(
                    f"SEMANTIC_VALIDATION_FAILURE: Verification failed on attempt {attempt + 1}. "
                    f"Error traceback: {str(e)}"
                )

                current_content = (
                    f"Original raw ticket context for extraction:\n<ticket>\n{user_content}\n</ticket>\n\n"
                    f"CRITICAL SYSTEM FEEDBACK: Your previous output failed local business-rule validation checks.\n"
                    f"The validator threw the following validation exception trace:\n"
                    f"--------------------------------------------------\n"
                    f"{str(e)}\n"
                    f"--------------------------------------------------\n\n"
                    f"Please re-analyze the original ticket context. Correct the specific contradiction or summary length "
                    f"issue mentioned above, and return a corrected schema payload."
                )

            except (TruncationException, RefusalException) as e:
                logger.critical(f"FATAL_PROTOCOL_ABORT: Aborting pipeline due to system/policy constraints: {type(e).__name__}")
                raise

            except Exception as e:
                logger.error(f"TRANSPORT_ABORT: Network-layer issue triggered pipeline abort: {type(e).__name__}")
                raise

        logger.critical(f"REPAIR_LIMIT_EXHAUSTED: Semantic processing failed after {max_retries + 1} executions.")
        raise RepairBudgetExhaustedError(
            f"Semantic execution failed to satisfy safety & business constraints. Last error: {last_error}"
        )