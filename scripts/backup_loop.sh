#!/bin/sh
set -eu

while true; do
  python scripts/backup_sqlite.py
  sleep "${BACKUP_INTERVAL_SECONDS:-86400}"
done
