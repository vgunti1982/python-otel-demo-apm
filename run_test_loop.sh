#!/usr/bin/env bash
set -e

echo "[runner] Running test_app.py once at $(date)"
# Run tests once and exit; return python's exit code if any
python test_app.py

echo "[runner] Completed. Exiting."
