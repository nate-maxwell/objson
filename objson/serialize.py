"""
# Serialization

* Description:

    Public API for serializing and deserializing Python values to and from JSON.
    Supports custom types registered via the @serializable decorator.
"""


from objson.lexer import Lexer
from objson.parser import Parser
from objson.registry import get_registry


_TYPE_KEY = '__type__'


# -----Dump--------------------------------------------------------------------

def dumps(value: object, indent: int = 0, depth: int = 0) -> str:
    """
    Serializes a Python value to a JSON string.

    Args:
        value (object): The value to serialize.
        indent (int): Number of spaces per indent level. 0 disables indentation.
        depth (int): Current recursion depth, used internally for indentation.
    Returns:
        str: The JSON string.
    """
    registry = get_registry()
    entry = registry.entry_for_type(type(value))
    if entry is not None:
        payload = entry.encode(value)
        payload[_TYPE_KEY] = entry.tag
        return dumps(payload, indent, depth)

    if value is None:
        return 'null'
    if isinstance(value, bool):
        return 'true' if value else 'false'
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    if isinstance(value, str):
        return _dump_string(value)
    if isinstance(value, list):
        return _dump_array(value, indent, depth)
    if isinstance(value, dict):
        return _dump_object(value, indent, depth)

    raise TypeError(f'Type {type(value).__name__!r} is not JSON serializable. '
                    f'Use @serializable to register it.')


def dump(value: object, fp, indent: int = 0) -> None:
    """
    Serializes a Python value to a JSON string and writes it to a file-like object.

    Args:
        value (object): The value to serialize.
        fp (IO[str]): A writable file-like object.
        indent (int): Number of spaces per indent level. 0 disables indentation.
    """
    fp.write(dumps(value, indent))


def _dump_string(value: str) -> str:
    escapes = {'"': '\\"', '\\': '\\\\', '\b': '\\b', '\f': '\\f',
               '\n': '\\n', '\r': '\\r', '\t': '\\t'}
    chars = []
    for ch in value:
        if ch in escapes:
            chars.append(escapes[ch])
        elif ord(ch) < 0x20:
            chars.append(f'\\u{ord(ch):04x}')
        else:
            chars.append(ch)
    return '"' + ''.join(chars) + '"'


def _dump_array(value: list, indent: int, depth: int) -> str:
    if not value:
        return '[]'
    items = [dumps(item, indent, depth + 1) for item in value]
    if not indent:
        return '[' + ', '.join(items) + ']'
    pad = ' ' * indent * (depth + 1)
    close_pad = ' ' * indent * depth
    return '[\n' + ',\n'.join(f'{pad}{item}' for item in items) + f'\n{close_pad}]'


def _dump_object(value: dict, indent: int, depth: int) -> str:
    if not value:
        return '{}'
    items = [dumps(k, indent, depth + 1) + ': ' + dumps(v, indent, depth + 1)
             for k, v in value.items()]
    if not indent:
        return '{' + ', '.join(items) + '}'
    pad = ' ' * indent * (depth + 1)
    close_pad = ' ' * indent * depth
    return '{\n' + ',\n'.join(f'{pad}{item}' for item in items) + f'\n{close_pad}}}'


# -----Load--------------------------------------------------------------------

def loads(text: str) -> object:
    """
    Deserializes a JSON string into a Python value.

    Args:
        text (str): The JSON string to deserialize.
    Returns:
        object: The deserialized Python value.
    """
    lexer = Lexer(text)
    parser = Parser(lexer)
    raw = parser.parse()
    return _decode_value(raw)


def load(fp) -> object:
    """
    Deserializes a JSON string from a file-like object into a Python value.

    Args:
        fp (IO[str]): A readable file-like object.
    Returns:
        object: The deserialized Python value.
    """
    return loads(fp.read())


def _decode_value(value: object) -> object:
    if isinstance(value, dict):
        return _decode_object(value)
    if isinstance(value, list):
        return [_decode_value(item) for item in value]
    return value


def _decode_object(value: dict) -> object:
    decoded = {k: _decode_value(v) for k, v in value.items()}

    tag = decoded.get(_TYPE_KEY)
    if not isinstance(tag, str):
        return decoded

    registry = get_registry()
    entry = registry.entry_for_tag(tag)
    if entry is None:
        raise ValueError(f'No type registered for tag {tag!r}.')

    payload = {k: v for k, v in decoded.items() if k != _TYPE_KEY}
    return entry.decode(payload)
