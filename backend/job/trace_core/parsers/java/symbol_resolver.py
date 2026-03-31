"""Resolves method call targets to fully qualified class names."""
from __future__ import annotations
from typing import Optional, Dict, TYPE_CHECKING
from trace_core.models.java_models import MethodCall, JavaClass

if TYPE_CHECKING:
    from trace_core.scanner.file_registry import FileRegistry


class SymbolResolver:
    """Resolves callee_class references to fully qualified names using import statements."""

    def resolve(
        self,
        method_call: MethodCall,
        context_class: JavaClass,
        class_index: Dict[str, JavaClass],
    ) -> Optional[str]:
        """Return the FQN of the callee class, or None if unresolvable."""
        callee = method_call.callee_class
        if not callee:
            return None

        # Already a FQN
        if "." in callee:
            return callee if callee in class_index else None

        # Check imports for matching simple name
        for imp in context_class.imports:
            if imp.endswith(f".{callee}") or imp.endswith(f"*"):
                candidate = imp if not imp.endswith("*") else f"{imp[:-1]}{callee}"
                if candidate in class_index:
                    return candidate

        # Same package
        same_pkg_fqn = f"{context_class.package}.{callee}"
        if same_pkg_fqn in class_index:
            return same_pkg_fqn

        # Scan all classes for simple name match
        for fqn, cls in class_index.items():
            if cls.simple_name == callee:
                return fqn

        return None
