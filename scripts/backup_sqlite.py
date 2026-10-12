"""Create atomic, rotating backups for a local SQLite database."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import sqlite3
import sys


def sqlite_database_path(database_url: str) -> Path:
    prefix = "sqlite+aiosqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("SQLite backups require a sqlite+aiosqlite DATABASE_URL")
    value = database_url.removeprefix(prefix)
    if value == ":memory:" or not value:
        raise ValueError("DATABASE_URL must point to a persistent SQLite file")
    return Path(value)


def prune_expired_backups(directory: Path, retention_days: int) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    for backup in directory.glob("vpnifi-*.db"):
        modified_at = datetime.fromtimestamp(backup.stat().st_mtime, timezone.utc)
        if modified_at < cutoff:
            backup.unlink()


def main() -> None:
    database_path = sqlite_database_path(os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///vpnifi.db"))
    if not database_path.is_file():
        raise FileNotFoundError(f"Database file not found: {database_path}")

    backup_dir = Path(os.environ.get("BACKUP_DIR", "backups"))
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    destination = backup_dir / f"vpnifi-{timestamp}.db"

    with sqlite3.connect(database_path) as source, sqlite3.connect(destination) as target:
        source.backup(target)
    prune_expired_backups(backup_dir, int(os.environ.get("BACKUP_RETENTION_DAYS", "14")))
    print(destination)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(f"Backup failed: {error}", file=sys.stderr)
        raise
