from typing import Callable, Iterable

def every[T](iterable: Iterable[T], predicate: Callable[[T], bool]) -> bool:
    """Check if all items in iterable satisfy the predicate."""
    return all(predicate(item) for item in iterable)


def some[T](iterable: Iterable[T], predicate: Callable[[T], bool]) -> bool:
    """Check if any item in iterable satisfies the predicate."""
    return any(predicate(item) for item in iterable)