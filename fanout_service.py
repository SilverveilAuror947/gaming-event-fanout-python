"""Fan out a player event to subscriber queues and acknowledge deliveries."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Iterable

from infrai_queue import QueueClient


@dataclass(frozen=True)
class PlayerAsset:
    asset_id: str
    owner_id: str
    kind: str


@dataclass(frozen=True)
class LiveEvent:
    event_id: str
    player_id: str
    asset: PlayerAsset
    action: str


@dataclass(frozen=True)
class ModerationItem:
    event_id: str
    queue: str
    reason: str


def fanout_event(client: QueueClient, event: LiveEvent, subscribers: Iterable[str]) -> int:
    """Publish one stable event record per subscriber; return publish count."""
    sent = 0
    for subscriber_id in subscribers:
        payload = {
            "event_id": event.event_id,
            "subscriber_id": subscriber_id,
            "player_id": event.player_id,
            "asset": asdict(event.asset),
            "action": event.action,
        }
        client.publish(payload)
        sent += 1
    return sent


def drain_moderation(client: QueueClient, limit: int = 20) -> list[dict]:
    """Read a moderation batch and acknowledge each message after processing."""
    batch = client.consume("moderation", max_messages=limit, visibility_timeout=60)
    messages = batch.get("messages") or []
    for message in messages:
        client.ack("moderation", message["message_id"])
    return messages


if __name__ == "__main__":
    queue = QueueClient()
    event = LiveEvent("match-42", "player-7", PlayerAsset("skin-9", "player-7", "cosmetic"), "created")
    print({"published": fanout_event(queue, event, ["feed", "moderation", "analytics"])})
    print({"acknowledged": len(drain_moderation(queue))})
