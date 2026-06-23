import json
import logging
from typing import Type, TypeVar, Any, Dict
from pydantic import BaseModel, TypeAdapter
import openai
from infrastructure.abstract_client import StructuredLLMClient, TruncationException, RefusalException

logger = logging.getLogger("sentinel_triage.infrastructure.openai")
T = TypeVar("T", bound=BaseModel)


class OpenAICompatibleClient(StructuredLLMClient):
    """
    An adapter implementing the StructuredLLMClient interface for OpenAI-compatible REST APIs.
    """

    def __init__(
            self,
            api_key: str,
            base_url: str = "https://api.openai.com/v1",
            model_name: str = "gpt-4o-mini",
    ):
        self.client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
        self.model_name = model_name

        logger.info(
            f"ADAPTER_INIT: OpenAICompatibleClient configured. "
            f"base_url={base_url!r}, model={model_name!r}"
        )

    async def raw_extract(
            self,
            schema: Type[T],
            system_instruction: str,
            user_content: str,
            temperature: float = 0.0
    ) -> Dict[str, Any]:
        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": user_content}
        ]

        adapter = TypeAdapter(schema)
        schema_dict = adapter.json_schema()

        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": schema.__name__,
                        "schema": schema_dict,
                        "strict": True
                    }
                }
            )
        except Exception as e:
            logger.error(f"TRANSPORT_EXCEPTION: Raw network layer communication failed: {str(e)}")
            raise

        choice = response.choices[0]

        if getattr(choice.message, "refusal", None):
            logger.warning("SAFETY_REFUSAL_TRIGGERED: Upstream content moderation blocked processing.")
            raise RefusalException(f"Safety Refusal: {choice.message.refusal}")

        if choice.finish_reason == "length":
            logger.error("METADATA_TRUNCATION_ERROR: Generated payload was truncated due to context limits.")
            raise TruncationException("The model ran out of tokens before completing the schema generation.")

        raw_json = choice.message.content
        if not raw_json:
            raise ValueError("The API returned an empty completion content payload.")

        try:
            return json.loads(raw_json)
        except json.JSONDecodeError as e:
            logger.critical("STRUCTURAL_PARSING_FAILURE: Upstream generated corrupted, unparseable JSON.")
            raise ValueError(f"Structural JSON parsing exception: {str(e)}")