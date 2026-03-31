"""Register all built-in prompt names into the PromptRegistry.

Templates themselves live in jinja_engine._INLINE_DEFAULTS (inline) or can be
overridden by placing a .j2 file in src/api/prompts/jinja_templates/<name>.j2.

No Python string templates are defined here any more — everything is Jinja2.
This file only handles registration of names.
"""
from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# All built-in prompt names.  Each corresponds to a Jinja2 template defined
# either in jinja_engine._INLINE_DEFAULTS or as a file on disk.
_BUILTIN_PROMPTS = [
    "business_derivation",  # plain-English derivation of how the field is populated
    "technical_summary",    # developer-oriented call-chain summary
    "reporting_logic",      # how the field drives report inclusion / categorisation
    "enrichment_logic",     # extraction → enrichment → override chain
    "downstream_impact",    # which fields, reports and systems depend on this field
    "examples",             # 5 worked trade scenarios exercising every branch
    "operations",           # production runbook: happy path, fallbacks, monitoring
    "field_impact",         # change impact analysis
    "chat_context",         # compact context block for chat queries
]


def register_default_prompts(registry: Any) -> None:
    """Register all built-in prompts into the given registry.

    Passing template_fn=None tells the registry to use the Jinja2 engine.
    """
    for name in _BUILTIN_PROMPTS:
        registry.register(name, template_fn=None)   # → Jinja2 engine
    logger.debug("Registered %d built-in Jinja2 prompts", len(_BUILTIN_PROMPTS))
