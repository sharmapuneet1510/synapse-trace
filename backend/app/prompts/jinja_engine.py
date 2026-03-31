"""Jinja2-powered prompt rendering engine.

Two rendering paths:
  1. Named template  — loaded from  src/api/prompts/jinja_templates/<name>.j2
                        with automatic fallback to inline defaults (no file needed).
  2. Custom string   — caller passes a raw Jinja2 template string; the same
                        context object is rendered into it.

Context variables available in every template
─────────────────────────────────────────────
  {{ field_name }}             str
  {{ trace_id }}               str
  {{ origin }}                 str  (XSLT | JAVA | XSLT_THEN_JAVA | UNKNOWN)
  {{ total_nodes }}            int
  {{ branch_count }}           int
  {{ has_xslt }}               bool
  {{ has_java }}               bool
  {{ pipeline_steps }}         list[str]
  {{ business_explanation }}   str
  {{ technical_explanation }}  str
  {{ nodes }}                  list[dict]  keys: label, node_type, transformation_type,
                                                  class_or_template, method, file, line
  {{ branches }}               list[dict]  keys: branch_id, condition, outcome
  {{ metadata }}               dict
  {{ downstream_name }}        str | None
  {{ downstream_packages }}    list[str]

Helper macros (imported via {% from '_macros.j2' import ... with context %})
  graph_summary()      — compact text block of the trace
  branch_table()       — markdown table of all branches
  node_list()          — markdown list of top-8 nodes
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from jinja2 import (
        Environment,
        FileSystemLoader,
        DictLoader,
        ChoiceLoader,
        StrictUndefined,
        TemplateNotFound,
        select_autoescape,
    )
    _JINJA2_AVAILABLE = True
except ImportError:
    _JINJA2_AVAILABLE = False

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "jinja_templates"


# ─────────────────────────────────────────────────────────────────────────────
# Context builder
# ─────────────────────────────────────────────────────────────────────────────

def build_context(result: Any) -> Dict[str, Any]:
    """Convert a TraceResult into a flat dict suitable for Jinja2 rendering."""
    s = result.summary

    nodes = []
    for n in result.nodes[:15]:  # cap to keep prompts reasonable
        nodes.append({
            "label": n.label,
            "node_type": n.node_type,
            "transformation_type": n.transformation_type.value if n.transformation_type else None,
            "class_or_template": n.evidence.class_or_template or "",
            "method": n.evidence.method_or_template_name or "",
            "file": os.path.basename(n.evidence.file_path) if n.evidence.file_path else "",
            "line": n.evidence.line_number or "",
            "condition": n.evidence.condition_text or "",
        })

    branches = []
    for b in result.branches[:10]:
        branches.append({
            "branch_id": b.branch_id,
            "condition": b.condition,
            "outcome": b.outcome or "n/a",
        })

    return {
        "field_name":            result.field_name,
        "trace_id":              result.trace_id,
        "origin":                s.origin.value,
        "total_nodes":           s.total_nodes,
        "branch_count":          s.branch_count,
        "has_xslt":              s.has_xslt,
        "has_java":              s.has_java,
        "pipeline_steps":        s.pipeline_steps,
        "business_explanation":  s.business_explanation,
        "technical_explanation": s.technical_explanation,
        "nodes":                 nodes,
        "branches":              branches,
        "metadata":              dict(result.metadata),
        "downstream_name":       result.metadata.get("downstream_name"),
        "downstream_packages":   result.metadata.get("downstream_packages", []),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Engine
# ─────────────────────────────────────────────────────────────────────────────

class JinjaPromptEngine:
    """Renders Jinja2 prompt templates with trace context.

    Template resolution order:
      1. File on disk at  src/api/prompts/jinja_templates/<name>.j2
      2. Inline default (defined in this module — works with no files at all)

    Usage
    -----
        engine = JinjaPromptEngine()

        # Named template (file or built-in default)
        prompt = engine.render_named("business_derivation", trace_result)

        # Ad-hoc Jinja2 string — same context variables
        prompt = engine.render_string(
            "Explain {{ field_name }} which has {{ branch_count }} branches.",
            trace_result,
        )
    """

    def __init__(self):
        if not _JINJA2_AVAILABLE:
            raise ImportError("jinja2 is required: pip install jinja2")
        self._env = self._build_env()

    # ── Public API ─────────────────────────────────────────────────────────────

    def render_named(self, name: str, result: Any) -> str:
        """Render the named template with the trace result context.

        Falls back to built-in inline defaults when no .j2 file exists.
        """
        context = build_context(result)
        template_name = name if name.endswith(".j2") else f"{name}.j2"
        try:
            tmpl = self._env.get_template(template_name)
        except TemplateNotFound:
            logger.debug(
                "JinjaEngine: '%s' not found on disk; using inline default", template_name
            )
            tmpl = self._env.get_template(f"_defaults/{template_name}")
        return tmpl.render(**context).strip()

    def render_string(self, template_str: str, result: Any) -> str:
        """Render an ad-hoc Jinja2 string with the trace result context.

        The same context variables are available as in named templates.
        The string can use any Jinja2 syntax including macros from _macros.j2:

            {% from '_macros.j2' import graph_summary with context %}
            {{ graph_summary() }}

            Your custom question about {{ field_name }}...
        """
        context = build_context(result)
        tmpl = self._env.from_string(template_str)
        return tmpl.render(**context).strip()

    def list_templates(self) -> list[str]:
        """Return names of all available templates (file + built-in)."""
        return [
            t for t in self._env.list_templates()
            if not t.startswith("_defaults/") and not t.startswith("_")
        ] + [
            t.replace("_defaults/", "").replace(".j2", "")
            for t in self._env.list_templates()
            if t.startswith("_defaults/")
        ]

    # ── Environment setup ─────────────────────────────────────────────────────

    def _build_env(self) -> "Environment":
        loaders = []

        # File-system loader — templates on disk override defaults
        if _TEMPLATES_DIR.exists():
            loaders.append(FileSystemLoader(str(_TEMPLATES_DIR)))

        # Inline defaults — always available
        loaders.append(DictLoader(_INLINE_DEFAULTS))

        env = Environment(
            loader=ChoiceLoader(loaders),
            undefined=StrictUndefined,
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        return env


# ─────────────────────────────────────────────────────────────────────────────
# Inline default templates  (used when no .j2 files exist on disk)
# ─────────────────────────────────────────────────────────────────────────────
# Keys must be prefixed with "_defaults/" so file templates take priority.

_MACROS = """\
{%- macro graph_summary() -%}
Field        : {{ field_name }}
Origin       : {{ origin }}
Total nodes  : {{ total_nodes }}
Branch count : {{ branch_count }}
Has XSLT     : {{ has_xslt }}
Has Java     : {{ has_java }}

Pipeline steps:
{% for step in pipeline_steps %}  {{ loop.index }}. {{ step }}
{% endfor %}
Key nodes:
{% for n in nodes[:8] %}  [{{ n.transformation_type or 'UNKNOWN' }}] {{ n.label }}  →  {{ n.class_or_template }}.{{ n.method }}
{% endfor %}
{% if branches %}
Conditional branches:
{% for b in branches[:5] %}  • {{ b.condition }}  →  {{ b.outcome }}
{% endfor %}
{% endif %}
{%- endmacro -%}

{%- macro branch_table() -%}
| Branch | Condition | Outcome |
|--------|-----------|---------|
{% for b in branches %}| `{{ b.branch_id }}` | {{ b.condition }} | {{ b.outcome }} |
{% endfor %}
{%- endmacro -%}

{%- macro node_list() -%}
{% for n in nodes[:8] %}- [{{ n.transformation_type or '?' }}] **{{ n.label }}** — `{{ n.class_or_template }}.{{ n.method }}` ({{ n.file }}:{{ n.line }})
{% endfor %}
{%- endmacro -%}
"""

_INLINE_DEFAULTS: dict = {
    # ── shared macros ────────────────────────────────────────────────────────
    "_macros.j2": _MACROS,

    # ── business_derivation ──────────────────────────────────────────────────
    "_defaults/business_derivation.j2": """\
{% from '_macros.j2' import graph_summary, branch_table with context %}
You are a regulatory reporting expert for capital markets.

A data lineage trace has been run for the output field **{{ field_name }}**.

--- TRACE SUMMARY ---
{{ graph_summary() }}

--- BRANCH CONDITIONS ---
{{ branch_table() }}

Task:
1. Explain in plain English (≤200 words) what business event or trade attribute
   **{{ field_name }}** captures.
2. Describe the derivation logic: under what conditions is each value set?
3. Identify any compliance or regulatory significance.
4. Flag data quality risks (null defaults, overrides, uncovered branches).

Respond in structured markdown:
## Purpose
## Derivation Logic
## Regulatory Significance
## Data Quality Risks
""",

    # ── technical_summary ────────────────────────────────────────────────────
    "_defaults/technical_summary.j2": """\
{% from '_macros.j2' import graph_summary, node_list with context %}
You are a senior software engineer reviewing a data lineage trace.

Field  : {{ field_name }}
Origin : {{ origin }}

--- TRACE ---
{{ graph_summary() }}

--- NODES ---
{{ node_list() }}

Task:
1. Which XSLT template first extracts/transforms **{{ field_name }}** and what XPath does it use?
2. Which Java class/method applies the final business logic?
3. The complete call chain from XSLT → Java.
4. Every conditional branch and its outcome.
5. Any overrides or fallback defaults.

Format as a numbered list of findings; include class names, method names, and line numbers.
""",

    # ── reporting_logic ──────────────────────────────────────────────────────
    "_defaults/reporting_logic.j2": """\
{% from '_macros.j2' import graph_summary, branch_table with context %}
You are a regulatory reporting expert for capital markets systems.

Field: {{ field_name }}

--- TRACE ---
{{ graph_summary() }}

--- BRANCHES ---
{{ branch_table() }}

Task:
1. Identify every conditional branch where the value of **{{ field_name }}** determines
   whether a trade is included/excluded from a regulatory report or how it is categorised.
2. List the specific report types / submission formats this field affects.
3. Describe reporting consequences of each possible value (Y / N / UNKNOWN / null).
4. Highlight jurisdiction-specific reporting differences visible in the trace.

Format:
## Report Inclusion Logic
## Report Categories Affected
## Value Consequences
## Jurisdiction Differences
""",

    # ── enrichment_logic ─────────────────────────────────────────────────────
    "_defaults/enrichment_logic.j2": """\
{% from '_macros.j2' import graph_summary, node_list with context %}
You are a senior Java developer reviewing a data enrichment pipeline.

Field: {{ field_name }}

The raw value is first extracted (XSLT), then enriched/overridden by Java logic.

--- TRACE ---
{{ graph_summary() }}

--- ENRICHMENT NODES ---
{{ node_list() }}

Task:
1. Identify the raw extraction source (XSLT variable / XPath expression).
2. List every Java class/method that enriches, transforms, or overrides the value.
3. Describe the enrichment chain in order: extraction → enrichment → override → final.
4. For each override: what triggers it, what value replaces the previous, in which class.
5. Identify any external data sources (lookup tables, rule engines).

Format:
## Raw Extraction
## Enrichment Chain
## Override Logic
## External Dependencies
""",

    # ── downstream_impact ────────────────────────────────────────────────────
    "_defaults/downstream_impact.j2": """\
{% from '_macros.j2' import graph_summary with context %}
You are a system architect performing a change impact analysis.

A change is being considered to **{{ field_name }}**.
{% if downstream_name %}Focus especially on downstream target: **{{ downstream_name }}**{% endif %}
{% if downstream_packages %}Downstream packages: {{ downstream_packages | join(', ') }}{% endif %}

--- CURRENT TRACE ---
{{ graph_summary() }}

Task:
1. Identify all downstream fields, calculations, or reports that depend on **{{ field_name }}**.
2. Identify downstream Java classes that consume this field's setter or getter.
3. Categorise impact: HIGH / MEDIUM / LOW.
4. List test scenarios to validate after any change.
5. Recommend a safe rollout strategy.

Format:
## Downstream Consumers
## Impact Categories
## Test Scenarios
## Rollout Strategy
""",

    # ── examples ─────────────────────────────────────────────────────────────
    "_defaults/examples.j2": """\
{% from '_macros.j2' import branch_table with context %}
You are a business analyst documenting a data lineage system.

Field: {{ field_name }}

--- BRANCH CONDITIONS ---
{{ branch_table() }}

--- PIPELINE ---
{% for step in pipeline_steps %}{{ loop.index }}. {{ step }}
{% endfor %}

Task:
Generate 5 concrete, realistic trade scenarios that exercise different branches.
For each scenario provide:
  - Trade description (instrument type, jurisdiction, key attributes)
  - Input values relevant to the derivation
  - Step-by-step derivation path through the logic
  - Final value of {{ field_name }}
  - Regulatory interpretation of that value

Format each as: ### Scenario N: [Title]
""",

    # ── operations ───────────────────────────────────────────────────────────
    "_defaults/operations.j2": """\
{% from '_macros.j2' import graph_summary with context %}
You are a production operations engineer for a regulatory reporting system.

Field: {{ field_name }}

--- TRACE ---
{{ graph_summary() }}

Task — provide an operational runbook entry:

1. **Happy Path**: Normal end-to-end flow when all inputs are present.
2. **Fallback / Default Paths**: When does the field fall back to a default?
   What value? Is it operationally acceptable?
3. **Override Mechanisms**: Every override point — where and when.
4. **Monitoring Signals**: Log lines, metrics, or alerts that indicate incorrect population.
5. **Common Operational Issues**: Known failure modes and resolution steps.

Format:
## Happy Path
## Fallback Paths
## Override Mechanisms
## Monitoring
## Common Issues
""",

    # ── field_impact ─────────────────────────────────────────────────────────
    "_defaults/field_impact.j2": """\
{% from '_macros.j2' import graph_summary, branch_table with context %}
You are a change impact analyst for a regulatory reporting system.

A developer is proposing to change the derivation logic for **{{ field_name }}**.

--- CURRENT TRACE ---
{{ graph_summary() }}

--- BRANCHES ---
{{ branch_table() }}

Task:
1. List all downstream consumers of **{{ field_name }}**.
2. Identify which conditional branches would be affected.
3. Assess the regulatory risk.
4. Suggest a safe testing approach.

Format:
## Downstream Impact
## Affected Branches
## Regulatory Risk
## Test Strategy
""",

    # ── chat_context ─────────────────────────────────────────────────────────
    "_defaults/chat_context.j2": """\
{% from '_macros.j2' import graph_summary with context %}
Context for answering questions about field {{ field_name }}:

{{ graph_summary() }}

Technical explanation:
{{ technical_explanation }}

Business explanation:
{{ business_explanation }}
""",
}

# Module-level singleton
jinja_engine = JinjaPromptEngine()
