"""LLM service — stub implementation with clear integration points.

HOW TO WIRE A REAL LLM
══════════════════════
Replace _call_llm() below with your provider's API call.
All eight graph methods (to_buissness_derivation, to_reporting_logic, …) and
the chat endpoint all funnel through this single method.

OpenAI / Azure OpenAI example:
────────────────────────────────────────────────────────────────
    from openai import AsyncOpenAI

    _client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])

    async def _call_llm(self, prompt: str, context: dict | None = None) -> str:
        resp = await _client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )
        return resp.choices[0].message.content

Anthropic Claude example:
────────────────────────────────────────────────────────────────
    import anthropic

    _client = anthropic.AsyncAnthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    async def _call_llm(self, prompt: str, context: dict | None = None) -> str:
        msg = await _client.messages.create(
            model="claude-opus-4-6",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text

AWS Bedrock example:
────────────────────────────────────────────────────────────────
    import boto3, json

    _bedrock = boto3.client("bedrock-runtime", region_name="us-east-1")

    async def _call_llm(self, prompt: str, context: dict | None = None) -> str:
        body = json.dumps({"prompt": prompt, "max_tokens_to_sample": 2048})
        resp = _bedrock.invoke_model(
            modelId="anthropic.claude-v2", body=body
        )
        return json.loads(resp["body"].read())["completion"]

The `context` dict (optional) carries extra metadata (trace_id, field_name, etc.)
that you can log or pass to the LLM as system context.
"""
from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)


class LLMService:
    """
    Central LLM integration point.

    All prompt-based graph methods and the chat endpoint call _call_llm().
    Replace that single method to switch between LLM providers.

    The higher-level helpers (generate_business_description, answer_chat_query)
    are thin wrappers kept for backwards compatibility with the chat router.
    """

    # ── STUB ─── replace this method with your real LLM call ─────────────────

    async def _call_llm(self, prompt: str, context: dict | None = None) -> str:
        """STUB: Replace this method body with your LLM API call.

        Parameters
        ----------
        prompt  : Fully rendered prompt string (from Jinja2 engine or registry).
        context : Optional extra metadata (trace_id, field_name, user_id, …).
                  Use this to add system context or for logging.

        Returns
        -------
        str — The LLM's response text.

        Notes
        -----
        - This method is async; use `await` when calling LLM SDKs that support it.
        - For synchronous SDKs, wrap with asyncio.to_thread() or run_in_executor().
        - See module docstring for OpenAI / Claude / Bedrock examples.
        """
        logger.warning(
            "LLMService._call_llm [STUB] — prompt_len=%d context=%s. "
            "Wire a real LLM in src/api/services/llm_service.py",
            len(prompt),
            list(context.keys()) if context else None,
        )
        # ── Stub response ─── remove everything below this line once wired ──
        field = (context or {}).get("field_name", "")
        snippet = prompt[:120].replace("\n", " ")
        return (
            f"[LLM Stub] field={field!r}\n\n"
            f"Prompt preview: {snippet}…\n\n"
            f"Wire a real LLM in src/api/services/llm_service.py._call_llm() "
            f"to get intelligent responses. See the module docstring for examples."
        )

    # ── Higher-level helpers (used by chat router) ────────────────────────────

    async def generate_business_description(
        self,
        field_name: str,
        jurisdiction_id: str,
        code_logic: str | None = None,
        xpaths: list[str] | None = None,
    ) -> str:
        logger.info(
            "generate_business_description: field='%s' jid='%s'",
            field_name, jurisdiction_id,
        )
        prompt_parts = [
            f"Explain the business purpose of field '{field_name}' "
            f"in {jurisdiction_id} regulatory reporting.",
        ]
        if code_logic:
            prompt_parts.append(f"\nCode logic:\n{code_logic}")
        if xpaths:
            prompt_parts.append(f"\nXPath expressions: {', '.join(xpaths)}")

        return await self._call_llm(
            "\n".join(prompt_parts),
            context={"field_name": field_name, "jurisdiction_id": jurisdiction_id},
        )

    async def answer_chat_query(
        self,
        question: str,
        jurisdiction_id: str | None = None,
        field_name: str | None = None,
        context: dict | None = None,
    ) -> str:
        logger.info(
            "answer_chat_query: jid='%s' field='%s' question_len=%d",
            jurisdiction_id, field_name, len(question),
        )
        ctx_parts = []
        if jurisdiction_id:
            ctx_parts.append(f"jurisdiction: {jurisdiction_id.upper()}")
        if field_name:
            ctx_parts.append(f"field: {field_name}")
        ctx_str = f" ({', '.join(ctx_parts)})" if ctx_parts else ""

        prompt = f"User question{ctx_str}:\n{question}"
        return await self._call_llm(
            prompt,
            context={
                "field_name": field_name,
                "jurisdiction_id": jurisdiction_id,
                **(context or {}),
            },
        )


llm_service = LLMService()
