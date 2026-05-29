# Store Intelligence Platform - Design Document

## Overview

This project implements a retail store intelligence platform that ingests customer movement events from CCTV analytics pipelines and exposes business metrics through REST APIs.

The system processes visitor interactions such as entry, zone dwell, billing queue participation, and purchase behavior to generate actionable store insights.

---

## Architecture

### Components

1. CCTV Analytics Pipeline
2. Event Ingestion API
3. SQLite Event Store
4. Analytics Engine
5. REST API Layer

### Data Flow

Video Stream
→ Detection & Tracking
→ Event Generation
→ POST /events/ingest
→ SQLite Storage
→ Metrics / Funnel / Heatmap / Anomalies APIs

---

## Event Processing

Each event follows the required schema:

* event_id
* store_id
* camera_id
* visitor_id
* event_type
* timestamp
* zone_id
* dwell_ms
* is_staff
* confidence
* metadata

Event IDs are globally unique UUID-v4 values.

Duplicate events are handled through idempotent ingestion using the event_id primary key.

---

## Storage Layer

SQLite is used as the persistence layer.

Advantages:

* Lightweight
* Zero operational overhead
* Suitable for challenge-scale workloads
* Easy Docker deployment

---

## Analytics

### Metrics

Calculates:

* Unique visitors
* Average dwell time per zone
* Queue depth
* Abandonment rate

### Funnel

Tracks:

* Entry
* Zone Visit
* Billing Queue
* Purchase

### Heatmap

Computes:

* Zone visits
* Average dwell time
* Relative heatmap score

### Anomalies

Current anomalies:

* QUEUE_SPIKE
* DEAD_ZONE

---

## Deployment

The application is containerized using Docker Compose.

Service:

* FastAPI API Server

Port:

* 8000

---

## Testing

Pytest is used for automated validation.

Coverage includes:

* Event ingestion
* Metrics calculations
* Anomaly detection
* Event schema validation
