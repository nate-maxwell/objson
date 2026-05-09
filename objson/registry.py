"""
# JSON Registry

* Description:

    Decorator and registry for custom type serialization.
    Classes decorated with @serializable can be round-tripped through dump/load.
"""


from typing import Callable
from typing import Protocol
from typing import runtime_checkable


# -----Protocol----------------------------------------------------------------

@runtime_checkable
class Serializable(Protocol):
    def __encode__(self) -> dict:
        ...

    @classmethod
    def __decode__(cls, data: dict) -> 'Serializable':
        ...


# -----Internal----------------------------------------------------------------

EncodeFunc = Callable[[object], dict]
DecodeFunc = Callable[[dict], object]


class _TypeEntry(object):
    def __init__(self, tag: str, type_: type, encode: EncodeFunc, decode: DecodeFunc) -> None:
        self.tag = tag
        self.type_ = type_
        self.encode = encode
        self.decode = decode


class Registry(object):
    def __init__(self) -> None:
        self._by_tag: dict[str, _TypeEntry] = {}
        self._by_type: dict[type, _TypeEntry] = {}

    def register(self, tag: str, type_: type, encode: EncodeFunc, decode: DecodeFunc) -> None:
        """
        Registers a type with the given tag and encode/decode functions.

        Args:
            tag (str): The unique string tag written into serialized output.
            type_ (type): The Python type being registered.
            encode (EncodeFunc): Callable that takes an instance and returns a
                plain dict.
            decode (DecodeFunc): Callable that takes a plain dict and returns
                an instance.
        """
        if tag in self._by_tag:
            raise ValueError(f'Tag {tag!r} is already registered.')
        if type_ in self._by_type:
            raise ValueError(f'Type {type_.__name__!r} is already registered.')
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

def serializable(tag: str) -> Callable[[type], type]:
    """Class decorator that registers a type for JSON serialization.

    The decorated class must implement the Serializable protocol:
        __encode__(self) -> dict
        __decode__(cls, data: dict) -> Serializable  (classmethod)

    Args:
        tag (str): The unique string tag used to identify this type in serialized output.

    Returns:
        Callable[[type], type]: The decorator function.
    """
    def decorator(cls: type) -> type:
        if not isinstance(cls, type) or not issubclass(cls, Serializable):
            raise TypeError(
                f'{cls.__name__!r} must implement the Serializable protocol '
                f'(__encode__ and __decode__).'
            )
        serializable_cls: Serializable = cls  # type: ignore[assignment]
        _registry.register(tag, cls, lambda instance: instance.__encode__(), serializable_cls.__decode__)
        return cls
    return decorator


def get_registry() -> Registry:
    """
    Returns the global type registry.

    Returns:
        Registry: The global registry instance.
    """
    return _registry
