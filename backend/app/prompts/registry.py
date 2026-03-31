"""PromptRegistry — maps named prompts to Jinja2 templates.

The registry is now backed by the JinjaPromptEngine.
Registering a name associates it with either:
  - a .j2 file on disk  (src/api/prompts/jinja_templates/<name>.j2)
  - an inline default   (defined in jinja_engine._INLINE_DEFAULTS)
  - a Python callable   (legacy path, still supported)

The primary API for all Graph methods:
  prompt_registry.render(name, trace_result)       → rendered str (Jinja2)
  prompt_registry.render_custom(tmpl, trace_result) → rendered str (ad-hoc Jinja2)
"""
from __future__ import annotations

import logging
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)


class PromptRegistry:
    """Central registry for named prompt templates.

    All nine built-in prompts delegate to the JinjaPromptEngine by default.
    Legacy Python-callable templates are still accepted for backwards compatibility.
    """

    def __init__(self) -> None:
        # name → None means "use JinjaEngine default"; Callable = legacy path
        self._registry: Dict[str, Optional[Callable[..., str]]] = {}

    # ── Registration ──────────────────────────────────────────────────────────

    def register(
        self,
        name: str,
        template_fn: Optional[Callable[..., str]] = None,
    ) -> None:
        """Register a prompt name.

        Pass template_fn=None  →  use the Jinja2 engine (default for all built-ins).
        Pass a callable        →  legacy Python f-string template (still works).
        """
        if name in self._registry:
            logger.debug("PromptRegistry: overwriting '%s'", name)
        self._registry[name] = template_fn
        logger.debug("PromptRegistry: registered '%s' (jinja=%s)", name, template_fn is None)

    # ── Rendering ─────────────────────────────────────────────────────────────

    def render(self, name: str, trace_result: Any) -> str:
        """Render a named prompt with the given TraceResult.

        Resolution order:
          1. If a Python callable was registered, call it (legacy).
          2. Otherwise delegate to JinjaPromptEngine.render_named().

        Raises KeyError if the name is not registered.
        """
        if name not in self._registry:
            raise KeyError(
                f"Prompt '{name}' not registered. Available: {self.list_prompts()}"
            )

        fn = self._registry[name]
        if fn is not None:
            # Legacy Python template callable
            logger.debug("PromptRegistry.render: '%s' via legacy callable", name)
            return fn(trace_result)

        # Jinja2 path
        from .jinja_engine import jinja_engine
        logger.info(
            "PromptRegistry.render: '%s' via Jinja2 engine for field '%s'",
            name, getattr(trace_result, "field_name", "?"),
        )
        return jinja_engine.render_named(name, trace_result)

    def render_custom(self, template_str: str, trace_result: Any) -> str:
        """Render an ad-hoc Jinja2 template string with the trace context.

        The same context variables are available as in named templates
        (field_name, origin, nodes, branches, pipeline_steps, …).

        Example
        -------
            result = prompt_registry.render_custom(
                "Field {{ field_name }} has {{ branch_count }} branches.\\n"
                "{% for b in branches %}  • {{ b.condition }}\\n{% endfor %}",
                trace_result,
            )
        """
        from .jinja_engine import jinja_engine
        logger.info(
            "PromptRegistry.render_custom: field='%s' template_len=%d",
            getattr(trace_result, "field_name", "?"),
            len(template_str),
        )
        return jinja_engine.render_string(template_str, trace_result)

    # ── Introspection ─────────────────────────────────────────────────────────

    def list_prompts(self) -> list[str]:
        """Return the names of all registered prompts."""
        return sorted(self._registry.keys())

    def __contains__(self, name: str) -> bool:
        return name in self._registry


prompt_registry = PromptRegistry()
