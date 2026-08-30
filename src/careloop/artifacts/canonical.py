"""Canonical JSON encoding and content hashing for frozen artifacts."""

import hashlib
import json
from collections.abc import Mapping, Sequence, Set
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel

type JsonScalar = str | int | float | bool | None
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]

HASH_EXCLUDED_FIELDS = frozenset({"canonical_hash", "runtime_metadata"})


def _to_json_value(value: object) -> JsonValue:
    if isinstance(value, BaseModel):
        return _to_json_value(value.model_dump(mode="json"))
    if isinstance(value, Enum):
        return _to_json_value(value.value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Mapping):
        converted: dict[str, JsonValue] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError("canonical JSON object keys must be strings")
            converted[key] = _to_json_value(item)
        return converted
    if isinstance(value, Set):
        raise TypeError("unordered sets cannot be encoded as canonical JSON")
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_to_json_value(item) for item in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError(f"unsupported canonical JSON value: {type(value).__name__}")


def _without_fields(value: JsonValue, excluded_fields: frozenset[str]) -> JsonValue:
    if isinstance(value, dict):
        return {
            key: _without_fields(item, excluded_fields)
            for key, item in value.items()
            if key not in excluded_fields
        }
    if isinstance(value, list):
        return [_without_fields(item, excluded_fields) for item in value]
    return value


def canonical_json_bytes(
    value: object, *, exclude_fields: frozenset[str] = frozenset()
) -> bytes:
    """Encode a JSON-compatible value using the frozen Milestone 2 rules."""
    json_value = _without_fields(_to_json_value(value), exclude_fields)
    encoded = json.dumps(
        json_value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return encoded.encode("utf-8")


def canonical_sha256(
    value: object, *, exclude_fields: frozenset[str] = HASH_EXCLUDED_FIELDS
) -> str:
    """Return a self-describing SHA-256 hash of canonical JSON content."""
    digest = hashlib.sha256(
        canonical_json_bytes(value, exclude_fields=exclude_fields)
    ).hexdigest()
    return f"sha256:{digest}"
