# Engineering Choices

## FastAPI

Chosen because:

* Automatic OpenAPI generation
* High performance
* Type-safe request validation
* Excellent developer experience

---

## SQLite

Chosen because:

* Lightweight
* Easy local deployment
* No external dependencies
* Sufficient for challenge requirements

Alternative considered:

* PostgreSQL

Rejected due to additional infrastructure complexity.

---

## UUID-based Idempotency

Each event uses UUID-v4 as event_id.

Benefits:

* Globally unique identifiers
* Duplicate protection
* Simple ingestion logic

---

## Docker

Docker Compose was selected to satisfy deployment requirements.

Benefits:

* Reproducible environment
* Consistent execution
* Easy evaluation by reviewers

---

## Testing Strategy

Pytest was selected.

Coverage includes:

* Event schema validation
* Ingestion behavior
* Metrics correctness
* Anomaly detection

---

## Current Limitations

* SQLite is not suitable for very high event throughput.
* Purchase correlation is currently simulated.
* CCTV pipeline integration is not yet implemented.

---

## Future Improvements

* PostgreSQL migration
* Redis caching
* Kafka event streaming
* YOLO-based visitor detection
* ByteTrack-based visitor tracking
* Real POS integration
* Advanced anomaly detection
