#!/bin/bash

set -e

echo "Generating CV events from videos..."
python -m pipeline.cv_events

echo "Sending CV events to API..."
python pipeline/ingest_cv.py

echo "Done."
