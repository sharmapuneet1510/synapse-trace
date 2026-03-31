"""Projects branch paths into a mind-map-ready JSON structure."""
from __future__ import annotations
from typing import List, Dict, Any
from trace_core.models.trace_models import BranchPath


class BranchProjector:
    """Converts BranchPath list into a UI-ready branch/mind-map JSON."""

    def project(self, branches: List[BranchPath]) -> Dict[str, Any]:
        """Return a dict suitable for the branch/mind-map visualization."""
        return {
            "branch_count": len(branches),
            "branches": [
                {
                    "branch_id": b.branch_id,
                    "condition": b.condition,
                    "outcome": b.outcome,
                    "node_count": len(b.nodes),
                    "nodes": [n.to_dict() for n in b.nodes],
                    "edges": [e.to_dict() for e in b.edges],
                }
                for b in branches
            ],
        }
