"""
# JSON Lexer

* Description:

    The primary scanner and lexical analyzer for JSON input.
"""


from typing import Optional

from objson.token import Token
from objson.token import TokenType
from objson.token import look_up_identifier


class Lexer(object):
    def __init__(self, input_text: str) -> None:
        self._text = input_text
        self._position: int = 0
        self._read_position: int = 0
        self._current_char: str = ''
        self._current_line_num: int = 1
        self._read_char()

    # -----Char Helpers--------------------------------------------------------

    def _read_char(self) -> None:
        if self._read_position >= len(self._text):
            self._current_char = '\0'
        else:
            self._current_char = self._text[self._read_position]

        self._position = self._read_position
        self._read_position += 1

    def _peek_char(self) -> str:
        if self._read_position >= len(self._text):
            return '\0'
        return self._text[self._read_position]

    def _skip_whitespace(self) -> None:
        while self._current_char in (' ', '\t', '\n', '\r'):
            if self._current_char == '\n':
                self._current_line_num += 1
            self._read_char()

    # -----Read Helpers--------------------------------------------------------

    def _read_string(self) -> Optional[tuple[str, Optional[str]]]:
        """
        Reads a double-quoted JSON string, handling escape sequences.

        Returns:
            tuple[str, str | None]: The string literal and an error message, or
            None if no error.
        """
        result = []
        escapes = {
            'b': '\b', 'f': '\f', 'n': '\n',
            'r': '\r', 't': '\t', '"': '"',
            '\\': '\\', '/': '/',
        }
        while True:
            self._read_char()
            ch = self._current_char
            if ch == '\0':
                return '', f'[Line {self._current_line_num}] Unterminated string.'
            if ch == '"':
                return ''.join(result), None

            if ch == '\\':
                self._read_char()
                esc = self._current_char
                if esc == 'u':
                    hex_chars = self._text[self._read_position:self._read_position + 4]
                    if len(hex_chars) < 4 or not all(c in '0123456789abcdefABCDEF' for c in hex_chars):
                        return '', f'[Line {self._current_line_num}] Invalid unicode escape.'
                    result.append(chr(int(hex_chars, 16)))
                    self._read_position += 4
                    self._position = self._read_position - 1
                    self._current_char = self._text[self._position] if self._position < len(self._text) else '\0'
                    continue
                if esc not in escapes:
                    return '', f'[Line {self._current_line_num}] Invalid escape character \\{esc}.'
                result.append(escapes[esc])
            else:
                result.append(ch)

    def _read_number(self) -> tuple[str, TokenType]:
        """
        Reads an integer or float number literal.

        Returns:
            tuple[str, TokenType]: The number literal and its token type
                (INT or FLOAT).
        """
        position = self._position
        is_float = False

        if self._current_char == '-':
            self._read_char()

        while self._current_char.isdigit():
            self._read_char()

        if self._current_char == '.':
            is_float = True
            self._read_char()
            while self._current_char.isdigit():
                self._read_char()

        if self._current_char in ('e', 'E'):
            is_float = True
            self._read_char()
            if self._current_char in ('+', '-'):
                self._read_char()
            while self._current_char.isdigit():
                self._read_char()

        literal = self._text[position:self._position]
        return literal, TokenType.FLOAT if is_float else TokenType.INT

    def _read_identifier(self) -> str:
        """
        Reads a bare identifier (used for keywords: true, false, null).

        Returns:
            str: The identifier string.
        """
        position = self._position
        while self._current_char.isalpha():
            self._read_char()
        return self._text[position:self._position]

    # -----Token Factory-------------------------------------------------------

    def _make_one_char_token(self, token_type: TokenType) -> Token:
        return Token(token_type, self._current_char, self._current_line_num)

    # -----Next Token----------------------------------------------------------

    def next_token(self) -> Token:
        """
        Scans the next token from the input.

        Returns:
            Token: The next token in the input stream.
        """
        self._skip_whitespace()

        ch = self._current_char

        if ch == '{':
            tok = self._make_one_char_token(TokenType.LBRACE)
        elif ch == '}':
            tok = self._make_one_char_token(TokenType.RBRACE)
        elif ch == '[':
            tok = self._make_one_char_token(TokenType.LBRACKET)
        elif ch == ']':
            tok = self._make_one_char_token(TokenType.RBRACKET)
        elif ch == ':':
            tok = self._make_one_char_token(TokenType.COLON)
        elif ch == ',':
            tok = self._make_one_char_token(TokenType.COMMA)

        elif ch == '"':
            literal, error = self._read_string()
            self._read_char()  # advance past the closing '"'
            if error is not None:
                return Token(TokenType.ILLEGAL, error, self._current_line_num)
            return Token(TokenType.STRING, literal, self._current_line_num)

        elif ch == '-' or ch.isdigit():
            literal, type_ = self._read_number()
            return Token(type_, literal, self._current_line_num)

        elif ch.isalpha():
            literal = self._read_identifier()
            type_ = look_up_identifier(literal)
            return Token(type_, literal, self._current_line_num)

        elif ch == '\0':
            tok = self._make_one_char_token(TokenType.EOF)
        else:
            tok = Token(TokenType.ILLEGAL, ch, self._current_line_num)

        self._read_char()
        return tok
