"""Recursion guard – prevents infinite loops in call-chain tracing."""
from __future__ import annotations
from modules.trace_core.logging.logger_factory import LoggerFactory
from .trace_context import TraceContext

logger = LoggerFactory.get("trace")


class RecursionGuard:
    """Manages visited-node tracking and depth checks."""

    @staticmethod
    def is_visited(node_id: str, ctx: TraceContext) -> bool:
        return node_id in ctx.visited_nodes

    @staticmethod
    def mark_visited(node_id: str, ctx: TraceContext):
        ctx.visited_nodes.add(node_id)

    @staticmethod
    def check_depth(ctx: TraceContext) -> bool:
        """Return True if depth is still within limit."""
        if ctx.depth_exceeded:
            logger.warning(
                f"Max recursion depth {ctx.max_depth} reached",
                trace_id=ctx.trace_id,
                field_name=ctx.field_name,
                recursion_depth=ctx.current_depth,
            )
            return False
        return True
