"""
# JSON Registry

* Description:

    Decorator and registry for custom type serialization.
    Classes decorated with @serializable can be round-tripped through dump/load.
"""

from typing import Any
from typing import Callable
from typing import Protocol
from typing import TypeVar
from typing import runtime_checkable

# -----Protocol----------------------------------------------------------------


@runtime_checkable
class Serializable(Protocol):
    def __encode__(self) -> dict: ...

    @classmethod
    def __decode__(cls, data: dict) -> "Serializable": ...


# -----Internal----------------------------------------------------------------

T = TypeVar("T")


class _TypeEntry(object):
    def __init__(
        self,
        tag: str,
        type_: type,
        encode: Callable[[Any], dict],
        decode: Callable[[dict], Any],
    ) -> None:
        self.tag = tag
        self.type_ = type_
        self.encode = encode
        self.decode = decode


def entry_for_type(registry: "Registry", instance: T) -> "_TypeEntryTyped[T] | None":
    """
    Returns the typed entry for a given instance's type, or None if not registered.

    Args:
        registry (Registry): The registry to look up from.
        instance (T): An instance of the type to look up.
    Returns:
        _TypeEntryTyped[T] | None: The matching entry, or None.
    """
    return registry._by_type.get(type(instance))  # type: ignore[return-value]


class _TypeEntryTyped(Protocol[T]):
    tag: str
    type_: type
    encode: Callable[[T], dict]
    decode: Callable[[dict], T]


# -----Registry----------------------------------------------------------------


class Registry(object):
    def __init__(self) -> None:
        self._by_tag: dict[str, _TypeEntry] = {}
        self._by_type: dict[type, _TypeEntry] = {}

    def register(
        self,
        tag: str,
        type_: type[T],
        encode: Callable[[T], dict],
        decode: Callable[[dict], T],
    ) -> None:
        """
        Registers a type with the given tag and encode/decode functions.

        Args:
            tag (str): The unique string tag written into serialized output.
            type_ (type[T]): The Python type being registered.
            encode (Callable[[T], dict]): Callable that takes an instance and
                returns a plain dict.
            decode (Callable[[dict], T]): Callable that takes a plain dict and
                returns an instance.
        """
        if tag in self._by_tag:
            raise ValueError(f"Tag {tag!r} is already registered.")
        if type_ in self._by_type:
            raise ValueError(f"Type {type_.__name__!r} is already registered.")
        entry = _TypeEntry(tag, type_, encode, decode)
        self._by_tag[tag] = entry
        self._by_type[type_] = entry

    def entry_for_tag(self, tag: str) -> _TypeEntry | None:
        """
        Returns the entry for a given tag, or None if not registered.

        Args:
            tag (str): The tag to look up.
        Returns:
            _TypeEntry | None: The matching entry, or None.
        """
        return self._by_tag.get(tag)

    def entry_for_type(self, type_: type) -> _TypeEntry | None:
        """
        Returns the entry for a given type, or None if not registered.

        Args:
            type_ (type): The type to look up.
        Returns:
            _TypeEntry | None: The matching entry, or None.
        """
        return self._by_type.get(type_)


_registry = Registry()


# -----Decorator---------------------------------------------------------------


def serializable(tag: str) -> Callable[[type[T]], type[T]]:
    """
    Class decorator that registers a type for JSON serialization.

    The decorated class must implement the Serializable protocol:
        __encode__(self) -> dict
        __decode__(cls, data: dict) -> Serializable  (classmethod)

    Args:
        tag (str): The unique string tag used to identify this type in serialized
            output.

    Returns:
        Callable[[type[T]], type[T]]: The decorator function.
    """

    def decorator(cls: type[T]) -> type[T]:
        if not isinstance(cls, type) or not issubclass(cls, Serializable):
            raise TypeError(
                f"{cls.__name__!r} must implement the Serializable protocol "
                f"(__encode__ and __decode__)."
            )
        serializable_cls: Serializable = cls  # type: ignore[assignment]

        def encode(instance: Any) -> dict:
            return instance.__encode__()

        _registry.register(tag, cls, encode, serializable_cls.__decode__)
        return cls

    return decorator


def get_registry() -> Registry:
    """
    Returns the global type registry.

    Returns:
        Registry: The global registry instance.
    """
    return _registry
