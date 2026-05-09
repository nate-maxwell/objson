"""
# Serialize Tests

* Description:

    Tests for the dumps/dump/loads/load public API, covering primitive
    round-trips, custom type serialization, indentation, file I/O,
    nested structures, and error cases.
"""

import io

import pytest

from objson.registry import serializable
from objson.serialize import dump
from objson.serialize import dumps
from objson.serialize import load
from objson.serialize import loads

# -----Fixtures----------------------------------------------------------------


@serializable("point")
class Point(object):
    def __init__(self, x: float, y: float) -> None:
        self.x = x
        self.y = y

    def __encode__(self) -> dict:
        return {"x": self.x, "y": self.y}

    @classmethod
    def __decode__(cls, data: dict) -> "Point":
        return cls(data["x"], data["y"])

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Point):
            return NotImplemented
        return self.x == other.x and self.y == other.y


@serializable("line")
class Line(object):
    def __init__(self, start: Point, end: Point) -> None:
        self.start = start
        self.end = end

    def __encode__(self) -> dict:
        return {"start": self.start, "end": self.end}

    @classmethod
    def __decode__(cls, data: dict) -> "Line":
        return cls(data["start"], data["end"])

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Line):
            return NotImplemented
        return self.start == other.start and self.end == other.end


# -----dumps: primitives-------------------------------------------------------


class TestDumpsPrimitives(object):
    def test_none(self) -> None:
        assert dumps(None) == "null"

    def test_true(self) -> None:
        assert dumps(True) == "true"

    def test_false(self) -> None:
        assert dumps(False) == "false"

    def test_integer(self) -> None:
        assert dumps(42) == "42"

    def test_negative_integer(self) -> None:
        assert dumps(-7) == "-7"

    def test_zero(self) -> None:
        assert dumps(0) == "0"

    def test_float(self) -> None:
        assert dumps(3.14) == repr(3.14)

    def test_negative_float(self) -> None:
        assert dumps(-2.5) == repr(-2.5)

    def test_string(self) -> None:
        assert dumps("hello") == '"hello"'

    def test_empty_string(self) -> None:
        assert dumps("") == '""'

    def test_bool_before_int(self) -> None:
        # bool is a subclass of int — must be checked first
        assert dumps(True) == "true"
        assert dumps(False) == "false"
        assert dumps(1) == "1"


# -----dumps: string escaping--------------------------------------------------


class TestDumpsStringEscaping(object):
    def test_escape_double_quote(self) -> None:
        assert dumps('say "hi"') == r'"say \"hi\""'

    def test_escape_backslash(self) -> None:
        assert dumps("a\\b") == r'"a\\b"'

    def test_escape_newline(self) -> None:
        assert dumps("a\nb") == r'"a\nb"'

    def test_escape_tab(self) -> None:
        assert dumps("a\tb") == r'"a\tb"'

    def test_escape_carriage_return(self) -> None:
        assert dumps("a\rb") == r'"a\rb"'

    def test_escape_backspace(self) -> None:
        assert dumps("a\bb") == r'"a\bb"'

    def test_escape_formfeed(self) -> None:
        assert dumps("a\fb") == r'"a\fb"'

    def test_escape_control_character(self) -> None:
        assert dumps("\x01") == '"\\u0001"'


# -----dumps: arrays-----------------------------------------------------------


class TestDumpsArrays(object):
    def test_empty_array(self) -> None:
        assert dumps([]) == "[]"

    def test_single_element(self) -> None:
        assert dumps([1]) == "[1]"

    def test_multiple_elements(self) -> None:
        assert dumps([1, 2, 3]) == "[1, 2, 3]"

    def test_mixed_types(self) -> None:
        assert dumps([1, "two", True, None]) == '[1, "two", true, null]'

    def test_nested_array(self) -> None:
        assert dumps([[1, 2], [3, 4]]) == "[[1, 2], [3, 4]]"


# -----dumps: objects----------------------------------------------------------


class TestDumpsObjects(object):
    def test_empty_object(self) -> None:
        assert dumps({}) == "{}"

    def test_single_key(self) -> None:
        assert dumps({"a": 1}) == '{"a": 1}'

    def test_multiple_keys(self) -> None:
        result = dumps({"a": 1, "b": 2})
        assert result == '{"a": 1, "b": 2}'

    def test_nested_object(self) -> None:
        assert dumps({"a": {"b": 1}}) == '{"a": {"b": 1}}'

    def test_object_with_array_value(self) -> None:
        assert dumps({"items": [1, 2]}) == '{"items": [1, 2]}'


# -----dumps: indentation------------------------------------------------------


class TestDumpsIndentation(object):
    def test_indented_array(self) -> None:
        result = dumps([1, 2], indent=2)
        assert result == "[\n  1,\n  2\n]"

    def test_indented_object(self) -> None:
        result = dumps({"a": 1}, indent=2)
        assert result == '{\n  "a": 1\n}'

    def test_indented_nested(self) -> None:
        result = dumps({"a": [1, 2]}, indent=2)
        assert result == '{\n  "a": [\n    1,\n    2\n  ]\n}'

    def test_zero_indent_is_compact(self) -> None:
        assert dumps([1, 2, 3], indent=0) == "[1, 2, 3]"

    def test_empty_array_not_indented(self) -> None:
        assert dumps([], indent=2) == "[]"

    def test_empty_object_not_indented(self) -> None:
        assert dumps({}, indent=2) == "{}"


# -----dumps: custom types-----------------------------------------------------


class TestDumpsCustomTypes(object):
    def test_custom_type_includes_type_key(self) -> None:
        result = dumps(Point(1.0, 2.0))
        assert '"__type__": "point"' in result

    def test_custom_type_includes_fields(self) -> None:
        result = dumps(Point(1.0, 2.0))
        assert '"x": 1.0' in result
        assert '"y": 2.0' in result

    def test_nested_custom_type(self) -> None:
        line = Line(Point(0.0, 0.0), Point(1.0, 1.0))
        result = dumps(line)
        assert '"__type__": "line"' in result
        assert '"__type__": "point"' in result

    def test_unregistered_type_raises(self) -> None:
        class Unregistered(object):
            pass

        with pytest.raises(TypeError, match="not JSON serializable"):
            dumps(Unregistered())

    def test_list_of_custom_types(self) -> None:
        result = dumps([Point(0.0, 0.0), Point(1.0, 1.0)])
        assert result.count('"__type__": "point"') == 2


# -----dump: file output-------------------------------------------------------


class TestDump(object):
    def test_dump_writes_to_file(self) -> None:
        fp = io.StringIO()
        dump({"a": 1}, fp)
        assert fp.getvalue() == '{"a": 1}'

    def test_dump_with_indent(self) -> None:
        fp = io.StringIO()
        dump([1, 2], fp, indent=2)
        assert fp.getvalue() == "[\n  1,\n  2\n]"

    def test_dump_custom_type(self) -> None:
        fp = io.StringIO()
        dump(Point(1.0, 2.0), fp)
        assert '"__type__": "point"' in fp.getvalue()


# -----loads: primitives-------------------------------------------------------


class TestLoadsPrimitives(object):
    def test_null(self) -> None:
        assert loads("null") is None

    def test_true(self) -> None:
        assert loads("true") is True

    def test_false(self) -> None:
        assert loads("false") is False

    def test_integer(self) -> None:
        assert loads("42") == 42

    def test_float(self) -> None:
        assert loads("3.14") == pytest.approx(3.14)

    def test_string(self) -> None:
        assert loads('"hello"') == "hello"

    def test_array(self) -> None:
        assert loads("[1, 2, 3]") == [1, 2, 3]

    def test_object(self) -> None:
        assert loads('{"a": 1}') == {"a": 1}


# -----loads: custom types-----------------------------------------------------


class TestLoadsCustomTypes(object):
    def test_decodes_registered_type(self) -> None:
        result = loads('{"__type__": "point", "x": 1.0, "y": 2.0}')
        assert isinstance(result, Point)

    def test_decoded_fields_correct(self) -> None:
        result = loads('{"__type__": "point", "x": 1.0, "y": 2.0}')
        assert isinstance(result, Point)
        assert result.x == pytest.approx(1.0)
        assert result.y == pytest.approx(2.0)

    def test_nested_custom_type(self) -> None:
        text = dumps(Line(Point(0.0, 0.0), Point(1.0, 1.0)))
        result = loads(text)
        assert isinstance(result, Line)
        assert isinstance(result.start, Point)
        assert isinstance(result.end, Point)

    def test_unknown_tag_raises(self) -> None:
        with pytest.raises(ValueError, match="No type registered"):
            loads('{"__type__": "ghost", "x": 1}')

    def test_plain_dict_with_no_type_key(self) -> None:
        result = loads('{"a": 1, "b": 2}')
        assert result == {"a": 1, "b": 2}

    def test_list_of_custom_types(self) -> None:
        text = dumps([Point(0.0, 0.0), Point(1.0, 1.0)])
        result = loads(text)
        assert isinstance(result, list)
        assert all(isinstance(p, Point) for p in result)


# -----load: file input--------------------------------------------------------


class TestLoad(object):
    def test_load_reads_from_file(self) -> None:
        fp = io.StringIO('{"a": 1}')
        assert load(fp) == {"a": 1}

    def test_load_custom_type(self) -> None:
        fp = io.StringIO('{"__type__": "point", "x": 1.0, "y": 2.0}')
        result = load(fp)
        assert isinstance(result, Point)


# -----round-trips-------------------------------------------------------------


class TestRoundTrips(object):
    def test_primitive_round_trips(self) -> None:
        for value in [None, True, False, 42, 3.14, "hello", [], {}]:
            assert loads(dumps(value)) == value

    def test_custom_type_round_trip(self) -> None:
        original = Point(1.5, 2.5)
        assert loads(dumps(original)) == original

    def test_nested_custom_type_round_trip(self) -> None:
        original = Line(Point(0.0, 0.0), Point(3.0, 4.0))
        assert loads(dumps(original)) == original

    def test_list_of_custom_types_round_trip(self) -> None:
        original = [Point(0.0, 0.0), Point(1.0, 1.0), Point(2.0, 2.0)]
        assert loads(dumps(original)) == original

    def test_complex_structure_round_trip(self) -> None:
        original = {
            "name": "shape",
            "origin": Point(0.0, 0.0),
            "edges": [
                Line(Point(0.0, 0.0), Point(1.0, 0.0)),
                Line(Point(1.0, 0.0), Point(1.0, 1.0)),
            ],
            "count": 2,
            "closed": True,
        }
        result = loads(dumps(original))
        assert isinstance(result, dict)
        assert result["name"] == "shape"
        assert isinstance(result["origin"], Point)
        assert all(isinstance(e, Line) for e in result["edges"])
        assert result["count"] == 2
        assert result["closed"] is True
