"""Collection utility helpers."""
from typing import List, TypeVar, Callable, Dict, Any, Iterable

T = TypeVar("T")
K = TypeVar("K")


def flatten(nested: List[List[T]]) -> List[T]:
    """Flatten one level of nesting."""
    return [item for sublist in nested for item in sublist]


def unique(items: Iterable[T]) -> List[T]:
    """Return unique items preserving insertion order."""
    seen = set()
    result = []
    for item in items:
        key = id(item) if not isinstance(item, (str, int, float, tuple, bool)) else item
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def group_by(items: List[T], key_fn: Callable[[T], K]) -> Dict[K, List[T]]:
    """Group a list of items by a key function."""
    result: Dict[K, List[T]] = {}
    for item in items:
        k = key_fn(item)
        result.setdefault(k, []).append(item)
    return result
