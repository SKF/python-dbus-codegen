"""Defines two operations on dbus type strings:

* `typehint(str)` generates a list of python type hints in string form,
  for adding to generated code templates.
* `instantiate(str)` returns a list of the default values of every type
  in the input string.

Both functions take an optional argument `dbus: bool` argument which,
when set, returns dbus types instead of python ones.

2019-09 JET
"""

from typing import Any, Dict, List, Sequence, Tuple, Type

from dbus import Signature
from dbus import types as dtype


def typehint(string: str, dbus=False) -> List[str]:
    "Get python type annotation for each type described in string"
    if dbus:
        types = _get_dbus_types(string)
    else:
        types = _get_types(string)
    return _string(types)


def instantiate(string: str, dbus=False) -> List[Any]:
    "Get default values for each type described in string"
    if dbus:
        types = _get_dbus_types(string)
    else:
        types = _get_types(string)
    return _instantiate(types)


_PRIMITIVES = {
    "ay": bytearray,  # ByteArray
    "b": bool,  # Boolean
    "d": float,  # Double
    "g": str,  # Signature
    "h": str,  # UnixFd
    "i": int,  # Int32
    "n": int,  # Int16
    "o": str,  # ObjectPath
    "q": int,  # UInt16
    "s": str,  # String
    "t": int,  # UInt64
    "u": int,  # UInt32
    "v": Any,  # Variant
    "x": int,  # Int64
    "y": int,  # Byte
}


def _get_types(s: str) -> List[Type]:
    signature = Signature(s)
    out = []
    for entry in signature:
        if entry in _PRIMITIVES:
            out.append(_PRIMITIVES[entry])
        elif entry.startswith("("):
            out.append(Tuple[tuple(_get_types(entry[1:-1]))])
        elif entry.startswith("a{"):
            out.append(Dict[tuple(_get_types(entry[2:-1]))])
        elif entry.startswith("a"):
            out.append(List[tuple(_get_types(entry[1:]))])

    return out


def _instantiate(types: Sequence[Type]) -> List[Any]:
    "instantiate every type in the collection types"
    out = []
    for typ in types:
        if isinstance(typ, list):
            out += _instantiate(typ)
        elif hasattr(typ, "__origin__"):
            # __origin__ is an attribute of typing._GenericAlias.
            # It points to the non-generic origin type that a type hint is
            # based on. Unlike the hint, the origin can be instantiated.
            # Tuples are a special case, since dbus structs are represented
            # using them and structs can not be empty.
            # FIXME: Python internals should NOT be used like this.
            if typ.__origin__ is tuple and typ.__args__:
                out.append(tuple(_instantiate(typ.__args__)))
            else:
                out.append(typ.__origin__())
        elif hasattr(typ, "__call__"):
            out.append(typ())
        else:
            # fallback for things that cannot be instantiated.
            # DBus container types are already constructed when they're passed in,
            # so they go here. MyPy rightly complains.
            out.append(typ)
    return out


def _string(types: Sequence[Type]) -> List[str]:
    "return the string representation of each type in types"
    out = []
    for typ in types:
        if isinstance(typ, (list, tuple)):
            out += _string(typ)
        elif isinstance(typ, type):
            out.append(typ.__name__)
        else:
            # if the user wants to generate type hints, assume typing is imported
            out.append(repr(typ).replace("typing.", ""))
    return out


_DBUS_PRIMITIVES = {
    "ay": dtype.ByteArray,
    "b": dtype.Boolean,
    "d": dtype.Double,
    "g": dtype.Signature,
    "h": dtype.UnixFd,
    "i": dtype.Int32,
    "n": dtype.Int16,
    "o": dtype.ObjectPath,
    "q": dtype.UInt16,
    "s": dtype.String,
    "t": dtype.UInt64,
    "u": dtype.UInt32,
    "v": str,  # Variant
    "x": dtype.Int64,
    "y": dtype.Byte,
}


def _get_dbus_types(s: str) -> List[Type]:
    signature = Signature(s)
    out = []
    for entry in signature:
        if entry in _DBUS_PRIMITIVES:
            if entry == "y":
                raise TypeError(
                    "dbus.Byte cannot be instantiated with default value! "
                    "Use ByteArray ('ay') or UInt16 ('q') instead."
                )
            out.append(_DBUS_PRIMITIVES[entry])
        # FIXME: DBus container types get instantiated here instead of in _instantiate.
        elif entry.startswith("("):
            defaults = _instantiate(_get_dbus_types(entry[1:-1]))
            out.append(dtype.Struct(defaults, signature=entry[1:-1]))
        elif entry.startswith("a{"):
            out.append(dtype.Dictionary(signature=entry[2:-1]))
        elif entry.startswith("a"):
            out.append(dtype.Array(signature=entry[1:]))

    return out
