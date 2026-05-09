"""
# Parser Tests

* Description:

    Tests for the JSON parser, covering all value types, nested structures,
    and error cases.
"""


import pytest

from objson.lexer import Lexer
from objson.parser import Parser


# -----Helpers-----------------------------------------------------------------

def parse(text: str) -> object:
    """
    Parses a JSON string and returns the resulting Python value.

    Args:
        text (str): The JSON input string.
    Returns:
        object: The parsed Python value.
    """
    return Parser(Lexer(text)).parse()


def parse_raises(text: str) -> str:
    """
    Asserts that parsing raises ValueError and returns the error message.

    Args:
        text (str): The JSON input string expected to fail.
    Returns:
        str: The error message from the raised ValueError.
    """
    with pytest.raises(ValueError) as exc_info:
        parse(text)
    return str(exc_info.value)


# -----Primitives--------------------------------------------------------------

class TestPrimitives(object):
    def test_true(self) -> None:
        assert parse('true') is True

    def test_false(self) -> None:
        assert parse('false') is False

    def test_null(self) -> None:
        assert parse('null') is None

    def test_string(self) -> None:
        assert parse('"hello"') == 'hello'

    def test_empty_string(self) -> None:
        assert parse('""') == ''

    def test_integer(self) -> None:
        assert parse('42') == 42

    def test_negative_integer(self) -> None:
        assert parse('-7') == -7

    def test_zero(self) -> None:
        assert parse('0') == 0

    def test_float(self) -> None:
        assert parse('3.14') == pytest.approx(3.14)

    def test_negative_float(self) -> None:
        assert parse('-2.5') == pytest.approx(-2.5)

    def test_scientific_notation(self) -> None:
        assert parse('1.5e3') == pytest.approx(1500.0)

    def test_scientific_notation_negative_exponent(self) -> None:
        assert parse('1.5e-3') == pytest.approx(0.0015)

    def test_integer_type(self) -> None:
        assert isinstance(parse('42'), int)

    def test_float_type(self) -> None:
        assert isinstance(parse('3.14'), float)

    def test_bool_is_not_int(self) -> None:
        # bool is a subclass of int in Python, so check type exactly
        assert type(parse('true')) is bool
        assert type(parse('false')) is bool


# -----Objects-----------------------------------------------------------------

class TestObjects(object):
    def test_empty_object(self) -> None:
        assert parse('{}') == {}

    def test_single_key(self) -> None:
        assert parse('{"a": 1}') == {'a': 1}

    def test_multiple_keys(self) -> None:
        assert parse('{"a": 1, "b": 2, "c": 3}') == {'a': 1, 'b': 2, 'c': 3}

    def test_string_value(self) -> None:
        assert parse('{"key": "value"}') == {'key': 'value'}

    def test_bool_value(self) -> None:
        assert parse('{"a": true, "b": false}') == {'a': True, 'b': False}

    def test_null_value(self) -> None:
        assert parse('{"key": null}') == {'key': None}

    def test_float_value(self) -> None:
        result = parse('{"x": 1.5}')
        assert isinstance(result, dict)
        assert result['x'] == pytest.approx(1.5)

    def test_nested_object(self) -> None:
        assert parse('{"a": {"b": 1}}') == {'a': {'b': 1}}

    def test_deeply_nested_object(self) -> None:
        assert parse('{"a": {"b": {"c": 42}}}') == {'a': {'b': {'c': 42}}}

    def test_object_with_array_value(self) -> None:
        assert parse('{"items": [1, 2, 3]}') == {'items': [1, 2, 3]}

    def test_preserves_key_order(self) -> None:
        result = parse('{"z": 1, "a": 2, "m": 3}')
        assert isinstance(result, dict)
        assert list(result.keys()) == ['z', 'a', 'm']

    def test_multiline_object(self) -> None:
        text = '{\n    "key": "value"\n}'
        assert parse(text) == {'key': 'value'}


# -----Arrays------------------------------------------------------------------

class TestArrays(object):
    def test_empty_array(self) -> None:
        assert parse('[]') == []

    def test_single_element(self) -> None:
        assert parse('[1]') == [1]

    def test_multiple_elements(self) -> None:
        assert parse('[1, 2, 3]') == [1, 2, 3]

    def test_string_elements(self) -> None:
        assert parse('["a", "b", "c"]') == ['a', 'b', 'c']

    def test_mixed_types(self) -> None:
        assert parse('[1, "two", true, false, null]') == [1, 'two', True, False, None]

    def test_nested_array(self) -> None:
        assert parse('[[1, 2], [3, 4]]') == [[1, 2], [3, 4]]

    def test_deeply_nested_array(self) -> None:
        assert parse('[[[1]]]') == [[[1]]]

    def test_array_of_objects(self) -> None:
        assert parse('[{"a": 1}, {"b": 2}]') == [{'a': 1}, {'b': 2}]

    def test_array_with_object(self) -> None:
        assert parse('[1, {"key": "val"}, 2]') == [1, {'key': 'val'}, 2]

    def test_preserves_order(self) -> None:
        assert parse('[3, 1, 2]') == [3, 1, 2]


# -----Nested------------------------------------------------------------------

class TestNested(object):
    def test_object_containing_array_containing_object(self) -> None:
        text = '{"items": [{"id": 1}, {"id": 2}]}'
        assert parse(text) == {'items': [{'id': 1}, {'id': 2}]}

    def test_array_containing_object_containing_array(self) -> None:
        text = '[{"tags": ["a", "b"]}]'
        assert parse(text) == [{'tags': ['a', 'b']}]

    def test_complex_nested_structure(self) -> None:
        text = '{"name": "root", "children": [{"name": "child", "value": 42}], "active": true}'
        assert parse(text) == {
            'name': 'root',
            'children': [{'name': 'child', 'value': 42}],
            'active': True,
        }


# -----Errors------------------------------------------------------------------

class TestErrors(object):
    def test_trailing_content(self) -> None:
        msg = parse_raises('true false')
        assert 'Unexpected trailing content' in msg

    def test_empty_input(self) -> None:
        parse_raises('')

    def test_object_missing_closing_brace(self) -> None:
        parse_raises('{"a": 1')

    def test_object_missing_colon(self) -> None:
        parse_raises('{"a" 1}')

    def test_object_missing_value(self) -> None:
        parse_raises('{"a":}')

    def test_object_missing_key_quotes(self) -> None:
        parse_raises('{a: 1}')

    def test_object_missing_comma(self) -> None:
        parse_raises('{"a": 1 "b": 2}')

    def test_array_missing_closing_bracket(self) -> None:
        parse_raises('[1, 2')

    def test_array_missing_comma(self) -> None:
        parse_raises('[1 2]')

    def test_illegal_token(self) -> None:
        msg = parse_raises('@')
        assert 'Illegal token' in msg

    def test_error_includes_line_number(self) -> None:
        msg = parse_raises('{\n"a" 1}')
        assert '[Line' in msg
