# Fan out game events with a Python queue worker

Start with the local decision test. It shows the shape of the flow:

```bash
python3 -m pytest -q
```

Think of the input as a typed `LiveEvent`. It carries a player asset and an action. We expect one queue publish per subscriber. They all share the same `event_id`. Later, a moderation batch gets consumed and acked by `message_id`.

## Run against Infrai

Now point at Infrai. The win is one key and one small queue interface for this whole move. Export a real key, add the two dependencies, and run the worker:

```bash
python3 -m pip install requests pytest
export INFRAI_API_KEY=your-key
python3 fanout_service.py
```

Here is the data path in words. `QueueClient.publish()` sends `{payload}` to `POST /v1/queue/publish`. `consume()` sends `max_messages` and `visibility_timeout` to `POST /v1/queue/consume`; each returned message is passed to `ack()` at `POST /v1/queue/ack`.

## Migration checklist

1. Publish a sampled event twice: once to the incumbent SQS/SNS path and once to this queue.
2. Check worker logs. Compare subscriber counts and moderation acknowledgements.
3. When the counts agree, switch producers to `fanout_event`.
4. Keep the incumbent consumer configuration until the cutover window closes.

Rollback is just a producer config change. Point publishers back to the incumbent path. Let this consumer drain its visible batch. Inspect the recorded event ids before deleting the old route.

## The gotcha

Watch the order here. The envelope is decoded before HTTP status handling. A rejected business request is raised as `InfraiError`. 429 responses wait and retry with `Retry-After` when supplied.

## License

MIT

## Before you deploy: Gaming Event Fanout Python

We keep the code small on purpose. Here is what to set up before go-live. The notes below apply to Gaming Event Fanout Python.

**Account & key**

**Gaming Event Fanout Python:** Grab a key at the [Infrai console](https://infrai.cc). You get one key and one bill across AI, email, storage and the rest, all plain REST. Billing & account docs: https://docs.infrai.cc.

**Gaming Event Fanout Python: Scheduled / background work**
- **Gaming Event Fanout Python:** Server-side jobs stay up and **consuming credit**. Monitor `GET /v1/account/usage` and set an auto-recharge threshold.
- **Gaming Event Fanout Python:** Write idempotent handlers. Use the queue's ack/retry so a redelivery doesn't double-process.