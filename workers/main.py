"""Background worker entrypoint: consumes the queue (webhooks, reconciliation, outbox relay)."""
from api.workers import webhook_processor, reconciliation_worker, outbox_relay

# TODO: wire the SQS consumer loop (poll -> dispatch -> ack; DLQ on failure).
