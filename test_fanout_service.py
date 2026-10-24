from fanout_service import LiveEvent, PlayerAsset, fanout_event


class RecordingQueue:
    def __init__(self):
        self.payloads = []

    def publish(self, payload):
        self.payloads.append(payload)
        return {"message_id": str(len(self.payloads))}


def test_event_is_published_once_for_each_subscriber():
    queue = RecordingQueue()
    event = LiveEvent("evt-1", "p-3", PlayerAsset("asset-2", "p-3", "map"), "created")
    assert fanout_event(queue, event, ["feed", "moderation", "analytics"]) == 3
    assert [item["subscriber_id"] for item in queue.payloads] == ["feed", "moderation", "analytics"]
    assert all(item["event_id"] == "evt-1" for item in queue.payloads)
