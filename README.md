# objson

A JSON parser and serializer for Python 3.10+ with support for custom type
round-trips via a decorator-based registry.

## Overview

objson is built from scratch around a handwritten lexer and recursive descent
parser. On top of that it adds a registry system that lets you teach the
serializer how to handle your own classes, so they survive a full
`dumps` → `loads` round-trip without any manual conversion.

## Quick Start

```python
from objson import dumps, loads

# Primitives
dumps({"name": "Nate", "score": 9.5, "active": True})
# '{"name": "Nate", "score": 9.5, "active": true}'

loads('{"name": "Nate", "score": 9.5, "active": true}')
# {'name': 'Nate', 'score': 9.5, 'active': True}
```

## Custom Types

Decorate a class with `@serializable` to register it. The class must implement
two methods:

- `__encode__(self) -> dict` — returns a plain dict of the instance's data
- `__decode__(cls, data: dict) -> Self` — classmethod that reconstructs an
  instance from that dict

```python
from objson.registry import serializable
from objson import dumps, loads


@serializable("vec3")
class Vec3:
    def __init__(self, x: float, y: float, z: float) -> None:
        self.x, self.y, self.z = x, y, z

    def __encode__(self) -> dict:
        return {"x": self.x, "y": self.y, "z": self.z}

    @classmethod
    def __decode__(cls, data: dict) -> "Vec3":
        return cls(data["x"], data["y"], data["z"])


v = Vec3(1.0, 2.0, 3.0)

serialized = dumps(v)
# '{"x": 1.0, "y": 2.0, "z": 3.0, "__type__": "vec3"}'

restored = loads(serialized)
# Vec3(1.0, 2.0, 3.0)
```

The `__type__` key is injected automatically by the serializer — your
`__encode__` and `__decode__` methods never need to handle it.

### Nested Custom Types

Custom types compose naturally. If a registered type contains another
registered type as a field, encode it directly and the serializer handles
the recursion:

```python
@serializable("transform")
class Transform:
    def __init__(self, position: Vec3, scale: float) -> None:
        self.position = position
        self.scale = scale

    def __encode__(self) -> dict:
        return {"position": self.position, "scale": self.scale}

    @classmethod
    def __decode__(cls, data: dict) -> "Transform":
        return cls(data["position"], data["scale"])


t = Transform(Vec3(1.0, 0.0, 0.0), 2.0)
restored = loads(dumps(t))
# Transform with a fully reconstructed Vec3 inside
```

### Indented Output

Pass `indent` to `dumps` or `dump` for pretty-printed output:

```python
dumps({"items": [1, 2, 3]}, indent=2)
# {
#   "items": [
#     1,
#     2,
#     3
#   ]
# }
```

## File I/O

```python
from objson import dump, load

# Write to file
with open("data.json", "w") as f:
    dump({"key": "value"}, f)

# Read from file
with open("data.json") as f:
    data = load(f)
```

## API Reference

### `dumps(value, indent=0) -> str`

Serializes a Python value to a JSON string. `indent` sets the number of spaces
per indentation level; `0` produces compact output.

### `dump(value, fp, indent=0) -> None`

Serializes a Python value and writes it to a writable file-like object.

### `loads(text) -> object`

Deserializes a JSON string into a Python value. Registered custom types are
reconstructed automatically.

### `load(fp) -> object`

Reads from a readable file-like object and deserializes the contents.

### `@serializable(tag)`

Class decorator that registers a type for serialization. `tag` is the unique
string written into the `__type__` field of the serialized output. Raises
`TypeError` at decoration time if `__encode__` or `__decode__` are missing.

### `entry_for_type(registry, instance) -> _TypeEntryTyped[T] | None`

Returns the typed registry entry for the type of the given instance, or `None`
if that type is not registered. Useful when you need to call `encode` or
`decode` directly with full type information.

```python
from objson.registry import entry_for_type, get_registry

entry = entry_for_type(get_registry(), Vec3(0.0, 0.0, 0.0))
if entry is not None:
    data = entry.encode(Vec3(1.0, 2.0, 3.0))   # -> {"x": 1.0, "y": 2.0, "z": 3.0}
    v = entry.decode({"x": 1.0, "y": 2.0, "z": 3.0})  # -> Vec3
```

## Supported JSON Types

| JSON       | Python           |
|------------|------------------|
| `null`     | `None`           |
| `true`     | `True`           |
| `false`    | `False`          |
| `number`   | `int` or `float` |
| `string`   | `str`            |
| `array`    | `list`           |
| `object`   | `dict`           |

String escape sequences supported: `\"`, `\\`, `\/`, `\b`, `\f`, `\n`, `\r`,
`\t`, `\uXXXX`.

## Error Handling

All errors raise standard Python exceptions with `[Line N]` prefixed messages
indicating where in the input the problem was found.

| Situation                                         | Exception    |
|---------------------------------------------------|--------------|
| Malformed JSON                                    | `ValueError` |
| Trailing content after value                      | `ValueError` |
| Unknown `__type__` tag on load                    | `ValueError` |
| Unregistered type passed to `dumps`               | `TypeError`  |
| `@serializable` on class missing protocol methods | `TypeError`  |
