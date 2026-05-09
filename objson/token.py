"""
# JSON Token Lib

* Description:

    The list of tokens recognized by the JSON lexer.
"""


from enum import Enum
from enum import unique


@unique
class TokenType(Enum):
    # ----------------------Misc-----------------------
    ILLEGAL = 'ILLEGAL'
    EOF = 'EOF'

    # -------------Identifiers + literals--------------
    STRING = 'STRING'
    INT = 'INT'
    FLOAT = 'FLOAT'

    # --------------------Keywords---------------------
    TRUE = 'TRUE'
    FALSE = 'FALSE'
    NULL = 'NULL'

    # --------------------Delimiters-------------------
    LBRACE = '{'
    RBRACE = '}'
    LBRACKET = '['
    RBRACKET = ']'
    COLON = ':'
    COMMA = ','


class Token(object):
    def __init__(self, type_: TokenType, literal: str, line_no: int) -> None:
        self.type_ = type_
        self.literal = literal
        self.line_no = line_no


keywords: dict[str, TokenType] = {
    'true': TokenType.TRUE,
    'false': TokenType.FALSE,
    'null': TokenType.NULL,
}
"""The literal keyword strings and their corresponding token types."""


def look_up_identifier(identifier: str) -> TokenType:
    """Returns the matching keyword token if the identifier is a keyword,
    otherwise returns ILLEGAL since bare identifiers are not valid JSON.

    Args:
        identifier (str): The identifier string to look up.

    Returns:
        TokenType: The matching keyword token type, or ILLEGAL.
    """
    if identifier in keywords:
        return keywords[identifier]
    return TokenType.ILLEGAL
