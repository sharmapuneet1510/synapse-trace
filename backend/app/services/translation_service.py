"""AI translation stub — converts code logic to business terms.

Currently returns placeholder content. Will be connected to LLM later.
"""
from __future__ import annotations

import logging

from ..schemas.translation import TranslationResult

logger = logging.getLogger(__name__)


class TranslationService:

    def explain(
        self,
        field_name: str,
        jurisdiction_id: str,
        code_snippet: str | None = None,
        xpaths: list[str] | None = None,
        dependencies: list[str] | None = None,
    ) -> TranslationResult:
        logger.info(
            "translate.explain: field='%s' jid='%s' xpaths=%d deps=%d [STUB]",
            field_name, jurisdiction_id,
            len(xpaths) if xpaths else 0,
            len(dependencies) if dependencies else 0,
        )
        dep_text = ", ".join(dependencies) if dependencies else "none identified"
        xpath_text = ", ".join(xpaths[:5]) if xpaths else "none"

        return TranslationResult(
            field_name=field_name,
            business_derivation=(
                f"BUSINESS PURPOSE: {field_name} is a critical field for "
                f"{jurisdiction_id.upper()} regulatory reporting. It determines "
                f"the contractual obligation and risk exposure calculation.\n\n"
                f"WHY IMPORTANT: This field is mandated under {jurisdiction_id.upper()} "
                f"jurisdiction rules. The trade data must have a valid value for "
                f"this field prior to submission.\n\n"
                f"REGULATORY REQUIREMENT: This field represents a core data point "
                f"for accurate position reporting and risk management.\n\n"
                f"SOURCE: Derived from internal trade capture system."
            ),
            reporting_logic=(
                f"Step 1: Check if {field_name} value exists in the source trade data.\n"
                f"Step 2: Validate against position table — compare current value "
                f"with previous submission. If changed, flag as amendment.\n"
                f"Step 3: Apply business date logic — use {field_name} as the "
                f"reference date for calculation windows.\n"
                f"Step 4: Format according to {jurisdiction_id.upper()} specification "
                f"(ISO 8601 for dates, standard precision for amounts).\n"
                f"Step 5: Populate the output message field."
            ),
            internal_enrichment=(
                f"DTCC XML Based → (DataPath)/Documents/SortByProductType/"
                f"Context/TradeData/TradeObject\n"
                f"NEWS JSON Based → {{{field_name}: \"value\"}}\n"
                f"ROBI File Based → {field_name}\n"
                f"TLM File Based → {field_name}"
            ),
            downstream_mapping=(
                f"The {field_name} field is consumed by the following downstream "
                f"systems:\n\n"
                f"• Regulatory Reporting Engine — final submission to "
                f"{jurisdiction_id.upper()}\n"
                f"• Position Management — daily position reconciliation\n"
                f"• Risk Analytics — exposure calculation inputs\n"
                f"• Audit Trail — historical change tracking\n\n"
                f"Dependencies: {dep_text}"
            ),
            examples=[
                (
                    f"EXAMPLE 1: Interest Rate IRS — A 5-year IRS traded on March 1st "
                    f"with a forward period. The {field_name} is populated from the "
                    f"trade capture system with the contract date. The system validates "
                    f"against the {jurisdiction_id.upper()} holiday calendar."
                ),
                (
                    f"EXAMPLE 2: Credit Default Swap — A corporate reference entity CDS "
                    f"is executed with a scheduled {field_name} value. The system "
                    f"extracts the value representing the protection period."
                ),
                (
                    f"EXAMPLE 3: Bermuda Bond Option — A bond option with termination "
                    f"mechanics uses {field_name} as the reference date for exercise "
                    f"periods per business requirements."
                ),
                (
                    f"EXAMPLE 4: FX Forward — The system computes available dates and "
                    f"selects the {field_name} value based on currency pair settlement "
                    f"conventions (T+1 or T+2)."
                ),
                (
                    f"EXAMPLE 5: Equity Swap — An equity swap uses {field_name} with "
                    f"staggered logic. The system calculates both counterparty views "
                    f"before settling on the final submitted value."
                ),
            ],
            operational_guidance=(
                f"WORKING SCENARIO 1: Maturity Processing — Operations team runs "
                f"end-of-day report. The {field_name} is verified against the "
                f"trade confirmation. If mismatch, escalate to Middle Office.\n\n"
                f"WORKING SCENARIO 2: Late Booking — If {field_name} is populated "
                f"after the reporting cutoff, the trade enters the next-day batch. "
                f"Operations must manually flag for same-day submission.\n\n"
                f"WORKING SCENARIO 3: Amendment — When {field_name} changes post-"
                f"initial submission, the system generates a correction message. "
                f"Operations verifies the delta before releasing.\n\n"
                f"WORKING SCENARIO 4: Regulatory Query — If the regulator queries "
                f"{field_name} value, Operations must trace back to the source "
                f"system trade record and provide the audit trail."
            ),
        )


# Singleton
translation_service = TranslationService()
