"""
# Lexer Tests

* Description:

    Tests for the JSON lexer, covering all token types, escape sequences,
    whitespace handling, line number tracking, and error cases.
"""


import pytest

from objson.lexer import Lexer
from objson.token import TokenType


# -----Helpers-----------------------------------------------------------------

def tokenize(text: str) -> list[tuple[TokenType, str]]:
    """Runs the lexer to completion and returns (type, literal) pairs, excluding EOF.

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


def tokenize_full(text: str) -> list[tuple[TokenType, str, int]]:
    """Runs the lexer to completion and returns (type, literal, line_no) triples, excluding EOF.

    Args:
        text (str): The input string to tokenize.

    Returns:
        list[tuple[TokenType, str, int]]: The type, literal, and line number for each token.
    """
    lexer = Lexer(text)
    tokens = []
    while True:
        tok = lexer.next_token()
        if tok.type_ == TokenType.EOF:
            break
        tokens.append((tok.type_, tok.literal, tok.line_no))
    return tokens


# -----Delimiters--------------------------------------------------------------

class TestDelimiters(object):
    def test_lbrace(self) -> None:
        assert tokenize('{') == [(TokenType.LBRACE, '{')]

    def test_rbrace(self) -> None:
        assert tokenize('}') == [(TokenType.RBRACE, '}')]

    def test_lbracket(self) -> None:
        assert tokenize('[') == [(TokenType.LBRACKET, '[')]

    def test_rbracket(self) -> None:
        assert tokenize(']') == [(TokenType.RBRACKET, ']')]

    def test_colon(self) -> None:
        assert tokenize(':') == [(TokenType.COLON, ':')]

    def test_comma(self) -> None:
        assert tokenize(',') == [(TokenType.COMMA, ',')]

    def test_all_delimiters_in_sequence(self) -> None:
        assert tokenize('{}[]:,') == [
            (TokenType.LBRACE, '{'),
            (TokenType.RBRACE, '}'),
            (TokenType.LBRACKET, '['),
            (TokenType.RBRACKET, ']'),
            (TokenType.COLON, ':'),
            (TokenType.COMMA, ','),
        ]


# -----Keywords----------------------------------------------------------------

class TestKeywords(object):
    def test_true(self) -> None:
        assert tokenize('true') == [(TokenType.TRUE, 'true')]

    def test_false(self) -> None:
        assert tokenize('false') == [(TokenType.FALSE, 'false')]

    def test_null(self) -> None:
        assert tokenize('null') == [(TokenType.NULL, 'null')]

    def test_unknown_identifier_is_illegal(self) -> None:
        tokens = tokenize('undefined')
        assert tokens == [(TokenType.ILLEGAL, 'undefined')]


# -----Strings-----------------------------------------------------------------

class TestStrings(object):
    def test_simple_string(self) -> None:
        assert tokenize('"hello"') == [(TokenType.STRING, 'hello')]

    def test_empty_string(self) -> None:
        assert tokenize('""') == [(TokenType.STRING, '')]

    def test_string_with_spaces(self) -> None:
        assert tokenize('"hello world"') == [(TokenType.STRING, 'hello world')]

    def test_escape_newline(self) -> None:
        assert tokenize(r'"line1\nline2"') == [(TokenType.STRING, 'line1\nline2')]

    def test_escape_tab(self) -> None:
        assert tokenize(r'"col1\tcol2"') == [(TokenType.STRING, 'col1\tcol2')]

    def test_escape_carriage_return(self) -> None:
        assert tokenize(r'"a\rb"') == [(TokenType.STRING, 'a\rb')]

    def test_escape_backspace(self) -> None:
        assert tokenize(r'"a\bb"') == [(TokenType.STRING, 'a\bb')]

    def test_escape_formfeed(self) -> None:
        assert tokenize(r'"a\fb"') == [(TokenType.STRING, 'a\fb')]

    def test_escape_solidus(self) -> None:
        assert tokenize(r'"a\/b"') == [(TokenType.STRING, 'a/b')]

    def test_escape_double_quote(self) -> None:
        assert tokenize(r'"say \"hi\""') == [(TokenType.STRING, 'say "hi"')]

    def test_escape_backslash(self) -> None:
        assert tokenize(r'"a\\b"') == [(TokenType.STRING, 'a\\b')]

    def test_unicode_escape(self) -> None:
        assert tokenize(r'"caf\u00e9"') == [(TokenType.STRING, 'café')]

    def test_unicode_escape_uppercase(self) -> None:
        assert tokenize(r'"caf\u00E9"') == [(TokenType.STRING, 'café')]

    def test_multiple_strings(self) -> None:
        assert tokenize('"foo" "bar"') == [
            (TokenType.STRING, 'foo'),
            (TokenType.STRING, 'bar'),
        ]

    def test_unterminated_string_is_illegal(self) -> None:
        tokens = tokenize('"hello')
        assert len(tokens) == 1
        assert tokens[0][0] == TokenType.ILLEGAL
        assert 'Unterminated string' in tokens[0][1]

    def test_invalid_escape_is_illegal(self) -> None:
        tokens = tokenize(r'"bad\q"')
        assert tokens[0] == (TokenType.ILLEGAL, '[Line 1] Invalid escape character \\q.')

    def test_invalid_unicode_escape_is_illegal(self) -> None:
        tokens = tokenize(r'"bad\u00zz"')
        assert tokens[0] == (TokenType.ILLEGAL, '[Line 1] Invalid unicode escape.')

    def test_short_unicode_escape_is_illegal(self) -> None:
        tokens = tokenize(r'"bad\u00"')
        assert tokens[0] == (TokenType.ILLEGAL, '[Line 1] Invalid unicode escape.')


# -----Integers----------------------------------------------------------------

class TestIntegers(object):
    def test_single_digit(self) -> None:
        assert tokenize('0') == [(TokenType.INT, '0')]

    def test_multi_digit(self) -> None:
        assert tokenize('42') == [(TokenType.INT, '42')]

    def test_negative(self) -> None:
        assert tokenize('-7') == [(TokenType.INT, '-7')]

    def test_negative_multi_digit(self) -> None:
        assert tokenize('-123') == [(TokenType.INT, '-123')]

    def test_large_integer(self) -> None:
        assert tokenize('1000000') == [(TokenType.INT, '1000000')]


# -----Floats------------------------------------------------------------------

class TestFloats(object):
    def test_simple_float(self) -> None:
        assert tokenize('3.14') == [(TokenType.FLOAT, '3.14')]

    def test_negative_float(self) -> None:
        assert tokenize('-2.5') == [(TokenType.FLOAT, '-2.5')]

    def test_scientific_lowercase_e(self) -> None:
        assert tokenize('1e10') == [(TokenType.FLOAT, '1e10')]

    def test_scientific_uppercase_e(self) -> None:
        assert tokenize('1E10') == [(TokenType.FLOAT, '1E10')]

    def test_scientific_positive_exponent(self) -> None:
        assert tokenize('1.5e+3') == [(TokenType.FLOAT, '1.5e+3')]

    def test_scientific_negative_exponent(self) -> None:
        assert tokenize('1.5e-3') == [(TokenType.FLOAT, '1.5e-3')]

    def test_negative_scientific(self) -> None:
        assert tokenize('-2.5e10') == [(TokenType.FLOAT, '-2.5e10')]


# -----Whitespace--------------------------------------------------------------

class TestWhitespace(object):
    def test_leading_spaces(self) -> None:
        assert tokenize('   true') == [(TokenType.TRUE, 'true')]

    def test_trailing_spaces(self) -> None:
        assert tokenize('true   ') == [(TokenType.TRUE, 'true')]

    def test_tabs(self) -> None:
        assert tokenize('\t\ttrue') == [(TokenType.TRUE, 'true')]

    def test_newlines(self) -> None:
        assert tokenize('\n\ntrue') == [(TokenType.TRUE, 'true')]

    def test_mixed_whitespace(self) -> None:
        assert tokenize(' \t\n true') == [(TokenType.TRUE, 'true')]

    def test_whitespace_between_tokens(self) -> None:
        assert tokenize('true , false') == [
            (TokenType.TRUE, 'true'),
            (TokenType.COMMA, ','),
            (TokenType.FALSE, 'false'),
        ]


# -----Line Numbers------------------------------------------------------------

class TestLineNumbers(object):
    def test_single_line(self) -> None:
        tokens = tokenize_full('true')
        assert tokens[0][2] == 1

    def test_token_on_second_line(self) -> None:
        tokens = tokenize_full('true\nfalse')
        assert tokens[0][2] == 1
        assert tokens[1][2] == 2

    def test_token_on_third_line(self) -> None:
        tokens = tokenize_full('1\n2\n3')
        assert tokens[2][2] == 3

    def test_multiple_blank_lines(self) -> None:
        tokens = tokenize_full('true\n\n\nfalse')
        assert tokens[1][2] == 4


# -----EOF---------------------------------------------------------------------

class TestEof(object):
    def test_empty_input_returns_eof(self) -> None:
        lexer = Lexer('')
        tok = lexer.next_token()
        assert tok.type_ == TokenType.EOF

    def test_whitespace_only_returns_eof(self) -> None:
        lexer = Lexer('   ')
        tok = lexer.next_token()
        assert tok.type_ == TokenType.EOF

    def test_eof_has_correct_literal(self) -> None:
        lexer = Lexer('')
        tok = lexer.next_token()
        assert tok.literal == '\0'


# -----Illegal-----------------------------------------------------------------

class TestIllegal(object):
    def test_unknown_character(self) -> None:
        tokens = tokenize('@')
        assert tokens == [(TokenType.ILLEGAL, '@')]

    def test_unknown_character_mid_stream(self) -> None:
        tokens = tokenize('true @ false')
        assert tokens[1] == (TokenType.ILLEGAL, '@')


# -----Full Structures---------------------------------------------------------

class TestFullStructures(object):
    def test_empty_object(self) -> None:
        assert tokenize('{}') == [
            (TokenType.LBRACE, '{'),
            (TokenType.RBRACE, '}'),
        ]

    def test_empty_array(self) -> None:
        assert tokenize('[]') == [
            (TokenType.LBRACKET, '['),
            (TokenType.RBRACKET, ']'),
        ]

    def test_simple_object(self) -> None:
        assert tokenize('{"key": "value"}') == [
            (TokenType.LBRACE, '{'),
            (TokenType.STRING, 'key'),
            (TokenType.COLON, ':'),
            (TokenType.STRING, 'value'),
            (TokenType.RBRACE, '}'),
        ]

    def test_simple_array(self) -> None:
        assert tokenize('[1, 2, 3]') == [
            (TokenType.LBRACKET, '['),
            (TokenType.INT, '1'),
            (TokenType.COMMA, ','),
            (TokenType.INT, '2'),
            (TokenType.COMMA, ','),
            (TokenType.INT, '3'),
            (TokenType.RBRACKET, ']'),
        ]

    def test_mixed_value_types(self) -> None:
        assert tokenize('[true, false, null, 42, 3.14, "hi"]') == [
            (TokenType.LBRACKET, '['),
            (TokenType.TRUE, 'true'),
            (TokenType.COMMA, ','),
            (TokenType.FALSE, 'false'),
            (TokenType.COMMA, ','),
            (TokenType.NULL, 'null'),
            (TokenType.COMMA, ','),
            (TokenType.INT, '42'),
            (TokenType.COMMA, ','),
            (TokenType.FLOAT, '3.14'),
            (TokenType.COMMA, ','),
            (TokenType.STRING, 'hi'),
            (TokenType.RBRACKET, ']'),
        ]

    def test_nested_object(self) -> None:
        assert tokenize('{"a": {"b": 1}}') == [
            (TokenType.LBRACE, '{'),
            (TokenType.STRING, 'a'),
            (TokenType.COLON, ':'),
            (TokenType.LBRACE, '{'),
            (TokenType.STRING, 'b'),
            (TokenType.COLON, ':'),
            (TokenType.INT, '1'),
            (TokenType.RBRACE, '}'),
            (TokenType.RBRACE, '}'),
        ]

    def test_multiline_object(self) -> None:
        text = '{\n    "key": "value"\n}'
        tokens = tokenize_full(text)
        assert tokens[0] == (TokenType.LBRACE, '{', 1)
        assert tokens[1] == (TokenType.STRING, 'key', 2)
        assert tokens[3] == (TokenType.STRING, 'value', 2)
        assert tokens[4] == (TokenType.RBRACE, '}', 3)
