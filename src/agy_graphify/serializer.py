"""Fast binary (msgspec) and JSON (orjson) serialization engine."""

from typing import Any, TypeVar

import msgspec
import orjson
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class SerializerEngine:
    """Provides ultra-fast C/Rust-backed binary (MsgPack) and JSON serialization."""

    @staticmethod
    def to_json_bytes(model: BaseModel) -> bytes:
        """Serialize Pydantic model to JSON bytes using orjson."""
        return orjson.dumps(model.model_dump())

    @staticmethod
    def to_msgpack_bytes(model: BaseModel) -> bytes:
        """Serialize Pydantic model to compact MsgPack binary bytes using msgspec."""
        return msgspec.msgpack.encode(model.model_dump())

    @staticmethod
    def from_msgpack_bytes(data: bytes, target_type: type[T]) -> T:
        """Deserialize MsgPack binary bytes back to Pydantic model using msgspec."""
        dict_data: dict[str, Any] = msgspec.msgpack.decode(data)
        return target_type.model_validate(dict_data)


__all__ = ["SerializerEngine"]
