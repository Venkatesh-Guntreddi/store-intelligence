# PROMPT:
# Generate pytest tests for the store intelligence event schema emitted by a CCTV pipeline.
#
# CHANGES MADE:
# Kept tests focused on required event schema validation before real video pipeline is added.

import pytest
from pydantic import ValidationError

from app.models import StoreEvent


def test_pipeline_event_schema_valid():
    event = StoreEvent(
        event_id="33333333-3333-4333-8333-333333333333",
        store_id="STORE_BLR_002",
        camera_id="CAM_ENTRY_01",
        visitor_id="VIS_TEST_001",
        event_type="ENTRY",
        timestamp="2026-03-03T14:20:00Z",
        zone_id=None,
        dwell_ms=0,
        is_staff=False,
        confidence=0.95,
        metadata={
            "queue_depth": None,
            "sku_zone": None,
            "session_seq": 1,
        },
    )

    assert event.store_id == "STORE_BLR_002"
    assert event.event_type == "ENTRY"
    assert event.confidence == 0.95


def test_pipeline_rejects_invalid_confidence():
    with pytest.raises(ValidationError):
        StoreEvent(
            event_id="44444444-4444-4444-8444-444444444444",
            store_id="STORE_BLR_002",
            camera_id="CAM_ENTRY_01",
            visitor_id="VIS_TEST_002",
            event_type="ENTRY",
            timestamp="2026-03-03T14:20:00Z",
            zone_id=None,
            dwell_ms=0,
            is_staff=False,
            confidence=1.5,
            metadata={},
        )

