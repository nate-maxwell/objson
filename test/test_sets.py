"""
# Set Tests

* Description:

    Tests for set support across the lexer, parser, and serializer.
"""

import pytest

from objson.lexer import Lexer
from objson.serialize import dumps
from objson.serialize import loads
from objson.token import TokenType

# -----Helpers-----------------------------------------------------------------


def tokenize(text: str) -> list[tuple[TokenType, str]]:
    """
    Runs the lexer to completion and returns (type, literal) pairs, excluding EOF.

    Args:
        text (str): The input string to tokenize.
    Returns:
        list[tuple[TokenType, str]]: The token type and literal for each token.
    """
    lexer = Lexer(text)
    tokens = []
    while True:
        tok = lexer.next_token()
        if tok.type_ == TokenType.EOF:
            break
        tokens.append((tok.type_, tok.literal))
    return tokens


def parse(text: str) -> object:
    """
    Parses a JSON string and returns the resulting Python value.

    Args:
        text (str): The JSON input string.
    Returns:
        object: The parsed Python value.
    """
    return loads(text)


# -----Tests-------------------------------------------------------------------


class TestLexerSets(object):
    def test_empty_set_token(self) -> None:
        assert tokenize("#{}") == [
            (TokenType.SET_LBRACE, "#{"),
            (TokenType.RBRACE, "}"),
        ]

    def test_set_lbrace_literal(self) -> None:
        tokens = tokenize("#{")
        assert tokens[0] == (TokenType.SET_LBRACE, "#{")

    def test_single_element_set_tokens(self) -> None:
        assert tokenize("#{1}") == [
            (TokenType.SET_LBRACE, "#{"),
            (TokenType.INT, "1"),
            (TokenType.RBRACE, "}"),
        ]

    def test_multi_element_set_tokens(self) -> None:
        assert tokenize("#{1, 2, 3}") == [
            (TokenType.SET_LBRACE, "#{"),
            (TokenType.INT, "1"),
            (TokenType.COMMA, ","),
            (TokenType.INT, "2"),
            (TokenType.COMMA, ","),
            (TokenType.INT, "3"),
            (TokenType.RBRACE, "}"),
        ]

    def test_string_element_tokens(self) -> None:
        assert tokenize('#{"a", "b"}') == [
            (TokenType.SET_LBRACE, "#{"),
            (TokenType.STRING, "a"),
            (TokenType.COMMA, ","),
            (TokenType.STRING, "b"),
            (TokenType.RBRACE, "}"),
        ]

    def test_hash_without_brace_is_illegal(self) -> None:
        tokens = tokenize("#")
        assert tokens[0] == (TokenType.ILLEGAL, "#")

    def test_hash_with_wrong_char_is_illegal(self) -> None:
        tokens = tokenize("#[")
        assert tokens[0] == (TokenType.ILLEGAL, "#")

    def test_set_followed_by_other_tokens(self) -> None:
        tokens = tokenize("#{1}, #{2}")
        assert tokens[0] == (TokenType.SET_LBRACE, "#{")
        assert tokens[4] == (TokenType.SET_LBRACE, "#{")


class TestParserSets(object):
    def test_empty_set(self) -> None:
        assert parse("#{}") == set()

    def test_empty_set_type(self) -> None:
        assert isinstance(parse("#{}"), set)

    def test_single_integer(self) -> None:
        assert parse("#{1}") == {1}

    def test_multiple_integers(self) -> None:
        assert parse("#{1, 2, 3}") == {1, 2, 3}

    def test_string_elements(self) -> None:
        assert parse('#{"a", "b", "c"}') == {"a", "b", "c"}

    def test_float_elements(self) -> None:
        result = parse("#{1.0, 2.0}")
        assert isinstance(result, set)
        assert 1.0 in result
        assert 2.0 in result

    def test_bool_elements(self) -> None:
        assert parse("#{true, false}") == {True, False}

    def test_null_element(self) -> None:
        assert parse("#{null}") == {None}

    def test_mixed_hashable_types(self) -> None:
        assert parse('#{1, "two", true, null}') == {1, "two", True, None}

    def test_set_in_array(self) -> None:
        result = parse("[#{1, 2}, #{3, 4}]")
        assert isinstance(result, list)
        assert {1, 2} in result
        assert {3, 4} in result

    def test_set_as_object_value(self) -> None:
        result = parse('{"tags": #{"a", "b"}}')
        assert isinstance(result, dict)
        assert result["tags"] == {"a", "b"}

    def test_missing_closing_brace_raises(self) -> None:
        with pytest.raises(ValueError):
            parse("#{1, 2")

    def test_missing_comma_raises(self) -> None:
        with pytest.raises(ValueError):
            parse("#{1 2}")


class TestSerializerSets(object):
    def test_empty_set(self) -> None:
        assert dumps(set()) == "#{}"

    def test_single_integer(self) -> None:
        assert dumps({42}) == "#{42}"

    def test_string_elements(self) -> None:
        result = dumps({"a"})
        assert result == '#{"a"}'

    def test_output_starts_with_set_sigil(self) -> None:
        assert dumps({1, 2, 3}).startswith("#{")

    def test_output_ends_with_brace(self) -> None:
        assert dumps({1, 2, 3}).endswith("}")

    def test_indented_empty_set(self) -> None:
        assert dumps(set(), indent=2) == "#{}"

    def test_indented_set(self) -> None:
        result = dumps({1}, indent=2)
        assert result == "#{\n  1\n}"

    def test_set_in_dict_dumps(self) -> None:
        result = dumps({"tags": {"a", "b"}})
        assert '"tags"' in result
        assert "#{" in result


class TestSetRoundTrips(object):
    def test_empty_set(self) -> None:
        assert loads(dumps(set())) == set()

    def test_integer_set(self) -> None:
        original = {1, 2, 3}
        assert loads(dumps(original)) == original

    def test_string_set(self) -> None:
        original = {"a", "b", "c"}
        assert loads(dumps(original)) == original

    def test_mixed_type_set(self) -> None:
        original = {1, "two", True}
        assert loads(dumps(original)) == original

    def test_set_in_list(self) -> None:
        original = [{1, 2}, {3, 4}]
        result = loads(dumps(original))
        assert isinstance(result, list)
        assert {1, 2} in result
        assert {3, 4} in result

    def test_set_as_dict_value(self) -> None:
        original = {"tags": {"x", "y", "z"}}
        result = loads(dumps(original))
        assert isinstance(result, dict)
        assert result["tags"] == {"x", "y", "z"}

    def test_result_is_set_type(self) -> None:
        assert isinstance(loads(dumps({1, 2, 3})), set)
