# ADR 0002: Database and State Management Strategy

**Date:** 2026-10-07  
**Status:** Accepted  
**Deciders:** Architecture Review Team

## Context

The PDF converter requires persistent storage for:
1. User accounts and organizational data
2. Job state (queued, validating, extracting, exporting, completed)
3. Document metadata and conversion history
4. Extracted document intermediate representation (IR)
5. Audit logs and usage metrics

State management must ensure:
- ACID properties for critical operations
- Idempotent task processing (Celery redelivery)
- Event sourcing pattern (outbox for durability)
- Efficient querying by tenant/user/job_status

## Decision

**Use PostgreSQL + SQLAlchemy + Alembic for persistent state.**

### Database Selection: PostgreSQL 15+

**Chosen for:**
- ACID guarantees for financial/critical data
- Outbox pattern support (transactions + publish)
- JSON columns for flexible metadata
- Full-text search (future enhancement)
- Column-level encryption (future)
- Mature hosting options

### ORM: SQLAlchemy 2.0

**Chosen for:**
- Type hints via sqlmodel (Pydantic + SQLAlchemy)
- Relationship management
- Query builder for complex filtering
- Migration support via Alembic

### State Patterns

**Outbox Pattern** (for durability):
```
job_created → save Job + OutboxEvent in same transaction
→ Worker polls events → publishes to queue → marks as sent
→ Even if queue fails, event persists until confirmed
```

**Job States**:
```
queued → validating → extracting → exporting → succeeded
                                     ↓
                            needs_review
                                     ↓
                                exported
                                     
                         (any) → cancelled
                         (any) → failed → expired
```

## Alternatives Considered

| Option | Advantages | Disadvantages | Verdict |
|--------|-----------|---------------|---------|
| **PostgreSQL + SQLAlchemy** | ACID; rich features; Outbox pattern | More complex than MongoDB | **Selected** |
| **MongoDB + Pymongo** | Flexible schema; fast write | No ACID; eventual consistency risks | Rejected |
| **SQLite** | Simple; local dev friendly | No concurrency; multiprocess issues | Rejected for prod |
| **DynamoDB/Firestore** | Serverless | No ACID; expensive query patterns | Rejected |

## Consequences

### Positive
- Strong consistency guarantees for job state
- Outbox pattern prevents lost events
- Type safety with SQLModel
- Built-in migration support
- Audit trail via event log

### Negative
- Requires operational monitoring (disk, replication)
- Schema migrations must be planned carefully
- Connection pooling must be tuned
- Slightly more complex than NoSQL for prototyping

## Implementation Details

### Core Tables
- `users` - User accounts and authentication
- `organizations` - Multi-tenant isolation
- `conversion_jobs` - Job state and metadata
- `documents` - Source PDF metadata
- `artifacts` - Output files (XLSX, DOCX, etc)
- `job_attempts` - Retry tracking
- `outbox_events` - Pending events to publish
- `audit_logs` - Compliance logging

### Schema Versioning
- Use Alembic for migrations
- Name migrations: `{timestamp}_{change_description}.py`
- Never use auto-generated migrations in production
- Test migrations down/up cycle
- Document breaking changes

### Backup Strategy
- Daily automated backups
- Point-in-time recovery to 30 days
- Test restore monthly
- Separate backup storage from live DB

## Related Decisions
- **ADR 0003**: Background Processing and Durability
- **ADR 0004**: Document IR Versioning and Storage

## References
- PostgreSQL Official: https://postgresql.org/
- SQLAlchemy 2.0: https://sqlalchemy.org/
- Alembic Migrations: https://alembic.sqlalchemy.org/
- Outbox Pattern: https://microservices.io/patterns/data/transactional-outbox.html
