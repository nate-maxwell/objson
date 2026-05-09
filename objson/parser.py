"""
# JSON Parser

* Description:

    The primary token parser that builds Python values from a JSON token stream.
"""

from objson.lexer import Lexer
from objson.token import Token
from objson.token import TokenType


class Parser(object):
    def __init__(self, lexer: Lexer) -> None:
        self._lexer = lexer

        self._current_token: Token = Token(TokenType.ILLEGAL, "", 0)
        self._peek_token: Token = Token(TokenType.ILLEGAL, "", 0)

        self._next_token()
        self._next_token()

    # -----Error Handling------------------------------------------------------

    def _peek_error(self, type_: TokenType) -> None:
        line_no = self._peek_token.line_no
        err = f"[Line {line_no}] Expected next token to be {type_}, got {self._peek_token.type_} instead."
        raise ValueError(err)

    def _current_token_error(self, type_: TokenType) -> None:
        line_no = self._current_token.line_no
        err = f"[Line {line_no}] Expected token to be {type_}, got {self._current_token.type_} instead."
        raise ValueError(err)

    def _illegal_token_error(self) -> None:
        line_no = self._current_token.line_no
        err = f"[Line {line_no}] Illegal token: {self._current_token.literal!r}."
        raise ValueError(err)

    def _unexpected_token_error(self) -> None:
        line_no = self._current_token.line_no
        err = f"[Line {line_no}] Unexpected token {self._current_token.type_} ({self._current_token.literal!r})."
        raise ValueError(err)

    # -----Token Handling------------------------------------------------------

    def _next_token(self) -> None:
        self._current_token = self._peek_token
        self._peek_token = self._lexer.next_token()

    def _current_token_is(self, type_: TokenType) -> bool:
        return self._current_token.type_ == type_

    def _peek_token_is(self, type_: TokenType) -> bool:
        return self._peek_token.type_ == type_

    def _expect_peek(self, type_: TokenType) -> None:
        """
        Advances to the next token if it matches the expected type, otherwise raises.

        Args:
            type_ (TokenType): The expected token type.
        """
        if self._peek_token_is(type_):
            self._next_token()
            return
        self._peek_error(type_)

    # -----Parse Entry---------------------------------------------------------

    def parse(self) -> object:
        """
        Parses the full JSON input and returns the root Python value.

        Returns:
            object: The parsed Python value.
        """
        value = self._parse_value()
        if not self._peek_token_is(TokenType.EOF):
            self._next_token()
            if not self._current_token_is(TokenType.EOF):
                line_no = self._current_token.line_no
                raise ValueError(f"[Line {line_no}] Unexpected trailing content after value.")
        return value

    # -----Value Dispatch------------------------------------------------------

    def _parse_value(self) -> object:
        """
        Dispatches to the correct parse method based on the current token.

        Returns:
            object: The parsed Python value.
        """
        if self._current_token_is(TokenType.LBRACE):
            return self._parse_object()
        elif self._current_token_is(TokenType.LBRACKET):
            return self._parse_array()
        elif self._current_token_is(TokenType.STRING):
            return self._parse_string_literal()
        elif self._current_token_is(TokenType.INT):
            return self._parse_integer_literal()
        elif self._current_token_is(TokenType.FLOAT):
            return self._parse_float_literal()
        elif self._current_token_is(TokenType.TRUE):
            return True
        elif self._current_token_is(TokenType.FALSE):
            return False
        elif self._current_token_is(TokenType.NULL):
            return None
        elif self._current_token_is(TokenType.ILLEGAL):
            self._illegal_token_error()
        else:
            self._unexpected_token_error()

    # -----Object Parsing------------------------------------------------------

    def _parse_object(self) -> dict:
        """
        Parses a JSON object into a Python dict.

        Returns:
            dict: The parsed dict.
        """
        result: dict = {}

        if self._peek_token_is(TokenType.RBRACE):
            self._next_token()
            return result

        while True:
            self._expect_peek(TokenType.STRING)
            key = self._current_token.literal

            self._expect_peek(TokenType.COLON)
            self._next_token()

            result[key] = self._parse_value()

            if self._peek_token_is(TokenType.RBRACE):
                self._next_token()
                return result
            elif not self._peek_token_is(TokenType.COMMA):
                self._peek_error(TokenType.COMMA)

            self._next_token()  # advance past COMMA

    # -----Array Parsing-------------------------------------------------------

    def _parse_array(self) -> list:
        """
        Parses a JSON array into a Python list.

        Returns:
            list: The parsed list.
        """
        result: list = []

        if self._peek_token_is(TokenType.RBRACKET):
            self._next_token()
            return result

        while True:
            self._next_token()
            result.append(self._parse_value())

            if self._peek_token_is(TokenType.RBRACKET):
                self._next_token()
                return result
            elif not self._peek_token_is(TokenType.COMMA):
                self._peek_error(TokenType.COMMA)

            self._next_token()  # advance past COMMA

    # -----Literal Parsing-----------------------------------------------------

    def _parse_string_literal(self) -> str:
        """
        Parses a STRING token into a Python str.

        Returns:
            str: The string value.
        """
        return self._current_token.literal

    def _parse_integer_literal(self) -> int:
        """
        Parses an INT token into a Python int.

        Returns:
            int: The integer value.
        """
        token = self._current_token
        try:
            return int(token.literal)
        except ValueError:
            raise ValueError(
                f"[Line {token.line_no}] Could not parse {token.literal!r} as integer."
            )

    def _parse_float_literal(self) -> float:
        """
        Parses a FLOAT token into a Python float.

        Returns:
            float: The float value.
        """
        token = self._current_token
        try:
            return float(token.literal)
        except ValueError:
            raise ValueError(f"[Line {token.line_no}] Could not parse {token.literal!r} as float.")
