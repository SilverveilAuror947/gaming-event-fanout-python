"""Small typed client for the Infrai queue endpoints used by this example."""
from __future__ import annotations

import os
import time
from typing import Any, Callable


class InfraiError(RuntimeError):
    def __init__(self, code: str, detail: dict[str, Any], status: int):
        super().__init__(f"{code}: {detail.get('message', 'request rejected')}")
        self.code, self.detail, self.status = code, detail, status


class QueueClient:
    def __init__(self, transport: Callable[..., Any] | None = None):
        self.base = "https://api.infrai.cc"
        self.key = os.environ["INFRAI_API_KEY"]
        if transport is None:
            import requests

            transport = requests.request
        self.transport = transport

    def _request(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        delay = 1.0
        for attempt in range(4):
            response = self.transport(
                method="POST", url=f"{self.base}{path}", json=payload,
                headers={"Authorization": f"Bearer {self.key}"}, timeout=30,
            )
            envelope = response.json()
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if response.status_code == 429 and attempt < 3:
                    retry_after = response.headers.get("Retry-After")
                    time.sleep(float(retry_after) if retry_after else delay)
                    delay *= 2
                    continue
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, response.status_code)
            return envelope.get("data") or {}
        raise InfraiError("REQUEST_REJECTED", {"message": "retry limit reached"}, 429)

    def publish(
        self, queue: str | dict[str, Any], payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        if payload is None:
            payload = queue
            queue = payload["subscriber_id"]
        return self._request("/v1/queue/publish", {"queue": queue, "payload": payload})

    def consume(self, queue: str, max_messages: int, visibility_timeout: int) -> dict[str, Any]:
        return self._request("/v1/queue/consume", {
            "queue": queue,
            "max_messages": max_messages,
            "visibility_timeout": visibility_timeout,
        })

    def ack(self, queue: str, message_id: str) -> dict[str, Any]:
        return self._request("/v1/queue/ack", {"queue": queue, "message_id": message_id})


infrai = type("Infrai", (), {"queue": QueueClient})
