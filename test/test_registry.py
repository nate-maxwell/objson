"""
# Registry Tests

* Description:

    Tests for the Registry class, Serializable protocol, and @serializable
    decorator. Uses isolated Registry instances to avoid global state
    contamination between tests.
"""


import pytest

from objson.registry import Registry
from objson.registry import Serializable
from objson.registry import entry_for_type
from objson.registry import serializable


# -----Fixtures----------------------------------------------------------------

@pytest.fixture
def registry() -> Registry:
    """
    Returns a fresh isolated Registry instance for each test.

    Returns:
        Registry: A new empty registry.
    """
    return Registry()


# -----Helpers-----------------------------------------------------------------

def make_encode(data: dict):
    """
    Returns an encode function that always returns the given dict.

    Args:
        data (dict): The dict to return from the encode function.
    """
    return lambda instance: data


def make_decode(instance: object):
    """
    Returns a decode function that always returns the given instance.

    Args:
        instance (object): The object to return from the decode function.
    """
    return lambda data: instance


# -----Registry.register-------------------------------------------------------

class TestRegistryRegister(object):
    def test_register_stores_entry_by_tag(self, registry: Registry) -> None:
        class A(object):
            pass

        registry.register('a', A, make_encode({}), make_decode(A()))
        assert registry.entry_for_tag('a') is not None

    def test_register_stores_entry_by_type(self, registry: Registry) -> None:
        class A(object):
            pass

        registry.register('a', A, make_encode({}), make_decode(A()))
        assert registry.entry_for_type(A) is not None

    def test_entry_has_correct_tag(self, registry: Registry) -> None:
        class A(object):
            pass

        registry.register('a', A, make_encode({}), make_decode(A()))
        assert registry.entry_for_tag('a').tag == 'a'

    def test_entry_has_correct_type(self, registry: Registry) -> None:
        class A(object):
            pass

        registry.register('a', A, make_encode({}), make_decode(A()))
        assert registry.entry_for_type(A).type_ is A

    def test_entry_encode_is_callable(self, registry: Registry) -> None:
        class A(object):
            pass

        registry.register('a', A, make_encode({'x': 1}), make_decode(A()))
        entry = registry.entry_for_tag('a')
        assert callable(entry.encode)

    def test_entry_decode_is_callable(self, registry: Registry) -> None:
        class A(object):
            pass

        registry.register('a', A, make_encode({}), make_decode(A()))
        entry = registry.entry_for_tag('a')
        assert callable(entry.decode)

    def test_duplicate_tag_raises(self, registry: Registry) -> None:
        class A(object):
            pass

        class B(object):
            pass

        registry.register('a', A, make_encode({}), make_decode(A()))
        with pytest.raises(ValueError, match="'a' is already registered"):
            registry.register('a', B, make_encode({}), make_decode(B()))

    def test_duplicate_type_raises(self, registry: Registry) -> None:
        class A(object):
            pass

        registry.register('a', A, make_encode({}), make_decode(A()))
        with pytest.raises(ValueError, match="'A' is already registered"):
            registry.register('b', A, make_encode({}), make_decode(A()))

    def test_multiple_types_can_be_registered(self, registry: Registry) -> None:
        class A(object):
            pass

        class B(object):
            pass

        registry.register('a', A, make_encode({}), make_decode(A()))
        registry.register('b', B, make_encode({}), make_decode(B()))
        assert registry.entry_for_tag('a') is not None
        assert registry.entry_for_tag('b') is not None


# -----Registry.entry_for_tag--------------------------------------------------

class TestEntryForTag(object):
    def test_returns_none_for_unknown_tag(self, registry: Registry) -> None:
        assert registry.entry_for_tag('missing') is None

    def test_returns_entry_for_known_tag(self, registry: Registry) -> None:
        class A(object):
            pass

        registry.register('a', A, make_encode({}), make_decode(A()))
        assert registry.entry_for_tag('a') is not None

    def test_tag_lookup_is_exact(self, registry: Registry) -> None:
        class A(object):
            pass

        registry.register('mytype', A, make_encode({}), make_decode(A()))
        assert registry.entry_for_tag('mytyp') is None
        assert registry.entry_for_tag('mytypes') is None


# -----Registry.entry_for_type-------------------------------------------------

class TestEntryForType(object):
    def test_returns_none_for_unknown_type(self, registry: Registry) -> None:
        class A(object):
            pass

        assert registry.entry_for_type(A) is None

    def test_returns_entry_for_known_type(self, registry: Registry) -> None:
        class A(object):
            pass

        registry.register('a', A, make_encode({}), make_decode(A()))
        assert registry.entry_for_type(A) is not None

    def test_does_not_match_subclass(self, registry: Registry) -> None:
        class A(object):
            pass

        class B(A):
            pass

        registry.register('a', A, make_encode({}), make_decode(A()))
        assert registry.entry_for_type(B) is None


# -----Serializable Protocol---------------------------------------------------

class TestSerializableProtocol(object):
    def test_class_with_both_methods_satisfies_protocol(self) -> None:
        class A(object):

            def __encode__(self) -> dict:
                return {}

            @classmethod
            def __decode__(cls, data: dict) -> 'A':
                return cls()

        assert isinstance(A(), Serializable)

    def test_class_missing_encode_does_not_satisfy_protocol(self) -> None:
        class A(object):

            @classmethod
            def __decode__(cls, data: dict) -> 'A':
                return cls()

        assert not isinstance(A(), Serializable)

    def test_class_missing_decode_does_not_satisfy_protocol(self) -> None:
        class A(object):
            def __encode__(self) -> dict:
                return {}

        assert not isinstance(A(), Serializable)

    def test_class_missing_both_does_not_satisfy_protocol(self) -> None:
        class A(object):
            pass

        assert not isinstance(A(), Serializable)


# -----@serializable decorator-------------------------------------------------

class TestSerializableDecorator(object):
    def test_decorator_returns_class_unchanged(self) -> None:
        @serializable('test_unchanged')
        class A(object):

            def __encode__(self) -> dict:
                return {}

            @classmethod
            def __decode__(cls, data: dict) -> 'A':
                return cls()

        assert A is A

    def test_decorator_registers_in_global_registry(self) -> None:
        from objson.registry import get_registry

        @serializable('test_registered')
        class A(object):

            def __encode__(self) -> dict:
                return {}

            @classmethod
            def __decode__(cls, data: dict) -> 'A':
                return cls()

        assert get_registry().entry_for_tag('test_registered') is not None
        assert get_registry().entry_for_type(A) is not None

    def test_decorator_missing_encode_raises(self) -> None:
        with pytest.raises(TypeError, match='Serializable protocol'):

            @serializable('test_no_encode')
            class A(object):

                @classmethod
                def __decode__(cls, data: dict) -> 'A':
                    return cls()

    def test_decorator_missing_decode_raises(self) -> None:
        with pytest.raises(TypeError, match='Serializable protocol'):

            @serializable('test_no_decode')
            class A(object):

                def __encode__(self) -> dict:
                    return {}

    def test_decorator_missing_both_raises(self) -> None:
        with pytest.raises(TypeError, match='Serializable protocol'):

            @serializable('test_no_methods')
            class A(object):
                pass

    def test_encode_function_calls_instance_encode(self) -> None:
        from objson.registry import get_registry

        @serializable('test_encode_call')
        class A(object):
            def __encode__(self) -> dict:
                return {'x': 99}

            @classmethod
            def __decode__(cls, _: dict) -> 'A':
                return cls()

        a = A()
        e = entry_for_type(get_registry(), a)
        assert e is not None
        assert e.encode(a) == {'x': 99}

    def test_decode_function_calls_class_decode(self) -> None:
        from objson.registry import get_registry

        @serializable('test_decode_call')
        class A(object):
            def __init__(self, x: int = 0) -> None:
                self.x = x

            def __encode__(self) -> dict:
                return {'x': self.x}

            @classmethod
            def __decode__(cls, data: dict) -> 'A':
                return cls(data['x'])

        e = entry_for_type(get_registry(), A())
        assert e is not None
        instance = e.decode({'x': 42})
        assert instance.x == 42
