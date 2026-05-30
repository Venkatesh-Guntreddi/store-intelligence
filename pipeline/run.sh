#!/bin/bash

set -e

API_URL=${API_URL:-http://localhost:8000}
EVENT_FILE=${EVENT_FILE:-data/generated_events.jsonl}

echo "Generating events from videos..."
python -m pipeline.detect --output "$EVENT_FILE"

echo "Sending events to API..."

python - <<PY
import json
import requests
from pathlib import Path

api_url = "$API_URL"
event_file = Path("$EVENT_FILE")

events = []

with event_file.open("r", encoding="utf-8") as f:
    for line in f:
        if line.strip():
            events.append(json.loads(line))

response = requests.post(
    f"{api_url}/events/ingest",
    json={"events": events},
    timeout=30,
)

print("Status:", response.status_code)
print(response.json())
PY

echo "Done."