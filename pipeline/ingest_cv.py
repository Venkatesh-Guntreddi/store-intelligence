import json
from pathlib import Path

import requests

events = []

with Path("data/cv_events.jsonl").open("r", encoding="utf-8") as f:
    for line in f:
        events.append(json.loads(line))

response = requests.post(
    "http://localhost:8000/events/ingest",
    json={"events": events},
    timeout=30,
)

print(response.status_code)
print(response.json())