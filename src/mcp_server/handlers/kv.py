from __future__ import annotations

import base64

__all__ = ["router"]

from fastapi import APIRouter, HTTPException, Response, Depends

from llmdb.kv import KV, RawValue
from llmdb.temporal_key import Key, pack

router = APIRouter()


def _decode_key(encoded: str) -> Key:
    user_key = base64.urlsafe_b64decode(encoded + "=")
    return (0, user_key, 0, 0)


@router.put("/kv/{key}")
async def put_value(key: str, body: dict[str, str], kv: KV = Depends()) -> Response:
    value = base64.urlsafe_b64decode(body["value"])
    kv.put(_decode_key(key), RawValue(payload=value))
    return Response(status_code=204)


@router.get("/kv/{key}")
async def get_value(key: str, kv: KV = Depends()) -> dict[str, str]:
    val = kv.get(_decode_key(key))
    if val is None:
        raise HTTPException(status_code=404)
    return {"value": base64.urlsafe_b64encode(val.payload).decode()}


@router.delete("/kv/{key}")
async def delete_value(key: str, kv: KV = Depends()) -> Response:
    encoded = pack(_decode_key(key))
    with kv.env.begin(write=True) as txn:
        if not txn.delete(encoded):
            raise HTTPException(status_code=404)
    return Response(status_code=204)
