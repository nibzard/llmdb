from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Literal, Union

__all__ = ["RawValue", "JSONValue", "Value", "encode", "decode"]


@dataclass(slots=True)
class RawValue:
    type_tag: ClassVar[Literal[0x00]] = 0x00
    payload: bytes = b""


@dataclass(slots=True)
class JSONValue:
    type_tag: ClassVar[Literal[0x01]] = 0x01
    payload: bytes = b""


Value = Union[RawValue, JSONValue]


def encode(value: Value) -> bytes:
    return bytes([value.type_tag]) + value.payload


def decode(data: bytes) -> Value:
    tag = data[0]
    payload = data[1:]
    if tag == RawValue.type_tag:
        return RawValue(payload=payload)
    if tag == JSONValue.type_tag:
        return JSONValue(payload=payload)
    raise ValueError(f"Unknown type tag: {tag}")
