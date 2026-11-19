# Event Payload Patterns

Normalize provider envelopes at the handler boundary, but preserve the original event ID, source, occurrence time, tenant context, trace context, schema version, and retry metadata. Never invent a new idempotency key during consumption.

## HTTP API Gateway

```json
{
  "version": "2.0",
  "routeKey": "POST /v1/jobs",
  "headers": {"authorization": "Bearer …", "idempotency-key": "01J..."},
  "requestContext": {"requestId": "req-123", "http": {"method": "POST", "path": "/v1/jobs"}},
  "body": "{\"tenantId\":\"t-1\",\"input\":{}}",
  "isBase64Encoded": false
}
```

**Idempotency key:** verified `Idempotency-Key` header scoped to authenticated tenant and route. For naturally idempotent reads, request ID is correlation only.

**Retry semantics:** gateways or clients may retry disconnects and 5xx responses. Cache the committed response for mutation keys. Reject key reuse with a different request hash.

## SQS and SNS-to-SQS

```json
{
  "Records": [{
    "messageId": "msg-123",
    "receiptHandle": "opaque",
    "body": "{\"eventId\":\"evt-9\",\"tenantId\":\"t-1\"}",
    "attributes": {"ApproximateReceiveCount": "2", "SentTimestamp": "1700000000000"},
    "messageAttributes": {"schemaVersion": {"dataType": "String", "stringValue": "2"}},
    "eventSource": "aws:sqs"
  }]
}
```

**Idempotency key:** prefer producer `eventId`; otherwise use queue ARN plus `messageId`. For SNS envelopes, use the SNS message ID and consumer purpose.

**Retry semantics:** at-least-once. Visibility timeout must exceed bounded processing. Return partial batch item failures when supported. Send exhausted messages to a DLQ with redrive and quarantine procedures.

## Kafka

```json
{
  "topic": "orders.v2",
  "partition": 7,
  "offset": 1842,
  "key": "tenant-1:order-9",
  "headers": {"event-id": "evt-9", "traceparent": "00-..."},
  "value": {"type": "OrderAccepted", "occurredAt": "2026-11-19T10:00:00Z", "data": {}}
}
```

**Idempotency key:** producer event ID is strongest. Topic-partition-offset identifies one log record but changes if an event is republished.

**Retry semantics:** offsets are committed after durable effects. Ordering exists only within a partition. Poison events need a governed retry/quarantine topic; do not block a partition forever.

## EventBridge

```json
{
  "version": "0",
  "id": "evt-123",
  "detail-type": "TenantProvisioned",
  "source": "com.example.controlplane",
  "account": "123456789012",
  "time": "2026-11-19T10:00:00Z",
  "region": "us-east-1",
  "resources": ["arn:example:tenant/t-1"],
  "detail": {"schemaVersion": "1", "tenantId": "t-1"}
}
```

**Idempotency key:** `source + id + consumer-purpose`.

**Retry semantics:** asynchronous targets are retried according to target policy; configure maximum age, attempts, and DLQ. Archive/replay means old successful events may return.

## S3 Object Event

```json
{
  "Records": [{
    "eventName": "ObjectCreated:Put",
    "eventTime": "2026-11-19T10:00:00Z",
    "s3": {
      "bucket": {"name": "tenant-uploads"},
      "object": {"key": "t-1/input/file.csv", "eTag": "abc", "sequencer": "006..."}
    }
  }]
}
```

**Idempotency key:** bucket, decoded object key, version ID when versioning is enabled, and transformation purpose. ETag is not always a content hash.

**Retry semantics:** notifications can be duplicated and may arrive out of order. Compare sequencers only for the same object key. Read current version deliberately rather than assuming the event points to latest.

## DynamoDB Streams

```json
{
  "Records": [{
    "eventID": "shard:sequence",
    "eventName": "MODIFY",
    "dynamodb": {
      "Keys": {"pk": {"S": "TENANT#t-1"}, "sk": {"S": "ORDER#9"}},
      "SequenceNumber": "123456",
      "StreamViewType": "NEW_AND_OLD_IMAGES",
      "NewImage": {},
      "OldImage": {}
    },
    "eventSourceARN": "arn:aws:dynamodb:...:stream/..."
  }]
}
```

**Idempotency key:** stream ARN plus event ID; add consumer purpose. Business-event IDs from an outbox item are preferable for downstream semantics.

**Retry semantics:** ordered per shard. Batch retries can replay successful records. Use partial batch response and bisect-on-error carefully; retain stream records long enough for recovery.

## Scheduled Event

```json
{
  "version": "0",
  "id": "schedule-invocation-id",
  "source": "aws.scheduler",
  "time": "2026-11-19T10:00:00Z",
  "detail-type": "Scheduled Event",
  "detail": {"job": "daily-reconciliation", "window": "2026-11-18"}
}
```

**Idempotency key:** logical job name plus intended schedule window, not delivery time. This permits safe reruns and prevents two deliveries from doing duplicate work.

**Retry semantics:** delayed and duplicate execution are possible. Define catch-up, overlap, missed-window, and late-data behavior. Use a lease only for coordination; preserve a durable completion record.

## Canonical Internal Envelope

```json
{
  "eventId": "stable-producer-id",
  "eventType": "OrderAccepted",
  "schemaVersion": "2",
  "source": "orders",
  "occurredAt": "2026-11-19T10:00:00Z",
  "tenantId": "t-1",
  "subject": "order/9",
  "traceparent": "00-...",
  "data": {}
}
```

Validate size, type, version, tenant binding, and authorization before domain processing. Log metadata and hashes rather than sensitive payloads.