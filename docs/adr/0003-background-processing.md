# ADR 0003: Background Processing Architecture

**Date:** 2026-10-07  
**Status:** Accepted  
**Deciders:** Architecture Review Team

## Context

PDF processing is CPU/memory-intensive and should not block API responses:
- Validation and format detection (I/O bound)
- Table extraction and OCR (CPU bound, 10-600 seconds per document)
- Format export (memory intensive)

Requirements:
1. Process large documents without blocking API
2. Handle retries and transient failures
3. Support multiple parallel workers
4. Enable monitoring and cancellation
5. Provide progress feedback to clients
6. Ensure idempotency (same job doesn't process twice)

## Decision

**Use Celery + RabbitMQ for background task processing.**

### Task Queue: Celery 5.3+

**Rationale:**
- Distributed task queue designed for Python
- First-class support for retries, timeouts, and dead-letters
- Integration with FastAPI via shared models
- Result backend (Redis) for job status
- Periodic tasks via Celery Beat

### Message Broker: RabbitMQ

**Rationale:**
- Reliable message delivery (AMQP protocol)
- Message acknowledgment prevents loss
- Dead-letter queues for failed tasks
- Management UI for monitoring
- No duplicates with proper configuration

### Architecture

```
API (FastAPI)
    ↓ [enqueue task + save job state]
Database (PostgreSQL)
    ↓ [outbox event]
Broker (RabbitMQ)
    ↓ [consume message]
Worker (Celery)
    ↓ [process PDF]
Storage (S3-compatible)
    ↓ [update job state]
Database (PostgreSQL)
    ↓ [client polls or SSE]
API (FastAPI)
    ↓
Client
```

### Task Categories

| Task Type | Priority | Timeout | Retry | Queue |
|-----------|----------|---------|-------|-------|
| Validate file | High | 30s | 2 | default |
| Extract content | Normal | 300s | 1 | processing |
| Export format | Normal | 180s | 1 | processing |
| OCR process | Low | 600s | 1 | ocr |
| Cleanup | Low | 60s | 3 | maintenance |

### Idempotency Pattern

```python
# Task receives unique job_id, attempt_id, generation
# Check if already completed: SELECT * FROM artifacts WHERE job_id AND generation
# If yes, return cached result
# If no, process and store atomically with generation
```

## Alternatives Considered

| Option | Advantages | Disadvantages | Verdict |
|--------|-----------|---------------|---------|
| **Celery + RabbitMQ** | Reliable; feature-rich; Python-native | Operational complexity | **Selected** |
| **Celery + Redis** | Simpler than RabbitMQ | Less reliable; loses messages on crash | Rejected |
| **APScheduler** | Simpler; in-process | Single machine; not distributed | Rejected |
| **AWS SQS + Lambda** | Serverless; managed | Vendor lock-in; cost unpredictable | Rejected |
| **Temporal.io** | Strong guarantees; observable | Overkill; operational burden | Future |

## Consequences

### Positive
- Decouples API from long-running computation
- Multiple workers process jobs in parallel
- Dead-letter queue captures failed tasks
- Clear separation of concerns
- Monitoring via Flower UI

### Negative
- Adds operational complexity (RabbitMQ cluster)
- Debugging distributed failures is harder
- Requires careful idempotency design
- Message ordering not guaranteed within partition

## Implementation Details

### Task Structure

```python
@celery_app.task(
    bind=True,
    max_retries=2,
    default_retry_delay=60,
    time_limit=600,  # Hard limit
    soft_time_limit=540,  # Graceful shutdown signal
    autoretry_for=(TransientError,),
    retry_kwargs={'max_retries': 2},
)
def process_pdf_conversion(
    self,
    job_id: str,
    attempt_id: str,
    generation: int,
):
    """Process a single PDF conversion job"""
    # Check if already completed (idempotency)
    # Process document
    # Store results atomically with generation
```

### Monitoring
- Flower Web UI (flower:5555)
- Prometheus metrics for task duration/failures
- Dead-letter queue alerts
- Worker health checks via Celery events

### Error Handling
- Transient errors: automatic retry with exponential backoff
- Permanent errors: move to dead-letter queue, notify user
- Timeout: force kill + retry once, then fail
- Out-of-memory: worker auto-restart, job rescheduled

## Related Decisions
- **ADR 0002**: Database and State Management
- **ADR 0005**: Process Isolation and Security

## References
- Celery Documentation: https://docs.celeryq.dev/
- RabbitMQ: https://www.rabbitmq.com/
- Flower Monitoring: https://flower.readthedocs.io/
- Idempotency Pattern: https://en.wikipedia.org/wiki/Idempotence
