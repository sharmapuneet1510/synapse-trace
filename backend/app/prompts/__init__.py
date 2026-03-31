"""Prompt system — Jinja2 templates + named registry + LLM stub.

Exports
-------
prompt_registry   — PromptRegistry  (register/render named prompts)
jinja_engine      — JinjaPromptEngine  (render named OR custom Jinja2 strings)

Quick reference
---------------
    from src.api.prompts import prompt_registry, jinja_engine

    # Named template (built-in Jinja2 default, overridable by .j2 file on disk)
    text = jinja_engine.render_named("business_derivation", trace_result)

    # Ad-hoc Jinja2 string — same context variables
    text = jinja_engine.render_string(
        "Explain {{ field_name }} which has {{ branch_count }} branches.",
        trace_result,
    )

    # Named prompt via legacy registry (still works)
    text = prompt_registry.render("business_derivation", trace_result)
"""
from .jinja_engine import jinja_engine
from .registry import prompt_registry
from .templates import register_default_prompts

register_default_prompts(prompt_registry)

__all__ = ["prompt_registry", "jinja_engine"]
