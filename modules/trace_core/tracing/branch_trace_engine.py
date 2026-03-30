"""Builds branch paths from traced nodes."""
from __future__ import annotations
import uuid
from typing import List, TYPE_CHECKING
from modules.trace_core.models.trace_models import TraceNode, TraceEdge, BranchPath
from modules.trace_core.models.common import EdgeRelationType

if TYPE_CHECKING:
    from .trace_context import TraceContext


class BranchTraceEngine:
    """Constructs BranchPath objects from condition-bearing nodes."""

    def build_branches(self, nodes: List[TraceNode], edges: List[TraceEdge], ctx: "TraceContext") -> List[BranchPath]:
        """Extract branch paths from nodes that carry condition metadata."""
        branches: List[BranchPath] = []

        for node in nodes:
            conditions = node.metadata.get("conditions", [])
            if not conditions:
                continue

            for condition in conditions:
                cond_text = condition.get("condition_text", "unknown condition")
                branch_type = condition.get("branch_type", "if")

                # True branch
                true_bid = str(uuid.uuid4())[:8]
                true_branch = BranchPath(
                    branch_id=true_bid,
                    condition=f"[{branch_type}] {cond_text} == TRUE",
                    nodes=[node],
                    outcome=condition.get("true_branch", "Y"),
                )
                branches.append(true_branch)

                # False/else branch
                false_bid = str(uuid.uuid4())[:8]
                false_branch = BranchPath(
                    branch_id=false_bid,
                    condition=f"[{branch_type}] {cond_text} == FALSE",
                    nodes=[node],
                    outcome=condition.get("false_branch", "N"),
                )
                branches.append(false_branch)

        # Ensure at least one default branch if we have nodes
        if nodes and not branches:
            branches.append(BranchPath(
                branch_id=str(uuid.uuid4())[:8],
                condition="DEFAULT",
                nodes=nodes,
                outcome="(single path)",
            ))

        return branches
