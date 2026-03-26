"""Stub LLM service. Replace _call_llm with your own API."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


class LLMService:
    """Stub LLM service. User will replace _call_llm with their own API."""

    async def _call_llm(self, prompt: str, context: dict | None = None) -> str:
        """STUB: Replace this method with your LLM API call.

        Example for OpenAI:
            response = openai.chat.completions.create(
                model="gpt-4", messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        """
        logger.warning(
            "_call_llm: STUB invoked — returning placeholder. "
            "Wire a real LLM in llm_service.py._call_llm(). "
            "Prompt length: %d chars", len(prompt),
        )
        return f"[LLM Stub Response] This is a placeholder response for: {prompt[:100]}..."

    async def generate_business_description(
        self,
        field_name: str,
        jurisdiction_id: str,
        code_logic: str | None = None,
        xpaths: list[str] | None = None,
    ) -> str:
        logger.info(
            "generate_business_description: field='%s' jid='%s' [STUB]",
            field_name, jurisdiction_id,
        )
        prompt = (
            f"Explain the business purpose of field '{field_name}' "
            f"in {jurisdiction_id} regulatory reporting..."
        )
        return (
            f"The field {field_name} serves as a key data point in "
            f"{jurisdiction_id.upper()} regulatory submissions. It captures "
            f"essential trade information required for compliance reporting "
            f"under the jurisdiction's regulatory framework.\n\n"
            f"Business Impact: This field directly affects the accuracy of "
            f"regulatory submissions and must be populated correctly to avoid "
            f"reporting discrepancies."
        )

    async def answer_chat_query(
        self,
        question: str,
        jurisdiction_id: str | None = None,
        field_name: str | None = None,
        context: dict | None = None,
    ) -> str:
        logger.info(
            "answer_chat_query: jid='%s' field='%s' question_len=%d [STUB]",
            jurisdiction_id, field_name, len(question),
        )
        ctx_parts = []
        if jurisdiction_id:
            ctx_parts.append(f"jurisdiction: {jurisdiction_id.upper()}")
        if field_name:
            ctx_parts.append(f"field: {field_name}")
        ctx_str = f" ({', '.join(ctx_parts)})" if ctx_parts else ""

        return (
            f"[Stub Response]{ctx_str}\n\n"
            f"Thank you for your question about{ctx_str}. "
            f"This is a placeholder response. Connect your LLM API in "
            f"llm_service.py._call_llm() to get intelligent answers.\n\n"
            f"Your question: {question}"
        )


llm_service = LLMService()
