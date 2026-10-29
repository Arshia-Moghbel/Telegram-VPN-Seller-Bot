# Vpnifi - Telegram VPN Seller Bot

A production-oriented Telegram bot for selling and managing VPN subscriptions, built with Python and aiogram.

Address: @Vpnifi26_bot

> **Status:** 🚧 In Active Development

## Overview

Vpnifi is a modular Telegram bot for selling and managing VPN subscriptions. The project is being developed with production-quality architecture in mind, making it suitable both as a real commercial service and as a portfolio project.

The long-term goal is to provide automatic VPN provisioning, payment processing, subscription management, and an extensible administration panel.

This project is in Persian.

## Features

### User
- User registration
- Browse VPN plans and tariffs
- Create orders
- Upload payment receipt
- Server overview
- Connection guides for Android, iOS, Windows, and macOS
- Support contact

### Admin
- Order management
- Payment verification
- Send VPN configurations
- Broadcast messages
- User management
- Sales statistics

## Tech Stack

- Python 3.12
- aiogram 3
- SQLAlchemy 2
- SQLite (development)
- PostgreSQL (planned)
- Git & GitHub

## Project Structure

```text
Telegram-VPN-Seller-Bot/
├── .github/
├── database/
├── deploy/
├── Filters/
├── handlers/
├── keyboards/
├── models/
├── scripts/
├── services/
├── states/
├── tests/
├── .dockerignore
├── .env.example
├── .gitattributes
├── .gitignore
├── CHANGELOG.md
├── CONTRIBUTING.md
├── Dockerfile
├── LICENSE
├── README.md
├── compose.yaml
├── config.py
├── db.py
├── main.py
├── requirements.txt
└── vpnifi.db
```

## Roadmap

### Version 0.1
- [x] Project structure
- [x] User registration
- [x] Database
- [x] Plans
- [x] Order model

### Version 0.2
- [x] Payment workflow
- [x] Receipt upload
- [x] Admin panel
- [x] Order management

### Version 0.3
- [x] PostgreSQL
- [x] Alembic
- [x] Docker
- [x] Logging

### Version 4.0
- [x] Automatic VPN provisioning workflow (ready for a future panel adapter)
- [x] Multiple VPN servers
- [x] Production deployment

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Version 4 readiness

The bot is ready to be connected to hosting when you buy it later. From the
admin panel, add each server with its location, protocol, priority and account
capacity; an approved order is assigned to the least-loaded eligible server.
No VPN credential, panel token or host is stored in the source code.

The existing manual configuration delivery remains active by design until a
specific VPN panel is selected. Automatic provisioning needs that panel's API
contract and credentials; this cannot be safely or truthfully enabled before a
server exists.

For a production deployment with PostgreSQL, set `POSTGRES_PASSWORD` in `.env`
along with the Telegram settings, then run from the repository root:

```bash
docker compose -f deploy/compose.production.yaml up -d --build
```

For an existing SQLite database, run `alembic stamp head` after taking a backup
so Alembic tracks future schema changes without recreating the current tables.

## Server deployment

The bot validates `BOT_TOKEN` and `ADMIN_ID` at startup and uses an instance
lock, so only one polling process can run on the same server. Copy
`.env.example` to `.env`, fill in the credentials, and keep `.env` private.

### Docker (recommended for one server)

```bash
docker compose up -d --build
docker compose logs -f bot
```

The Compose configuration stores the SQLite database in `./data` and creates a
rotating backup in `./backups` once per day. Change `BACKUP_RETENTION_DAYS` or
`BACKUP_INTERVAL_SECONDS` in `.env` if needed. Check service health with:

```bash
docker compose ps
```

Direct local execution uses the database URL from `.env` (by default,
`./vpnifi.db`); Docker uses `./data/vpnifi.db`. Both persist through restarts,
but they are separate databases. Choose one mode for real operation. If you
move from local execution to Docker, copy the existing database once before
the first Docker start:

```bash
mkdir -p data
cp vpnifi.db data/vpnifi.db
```

### systemd

For a non-Docker Linux server, adapt
`deploy/systemd/vpnifi.service` for the service user and installation path,
then install and enable it:

```bash
sudo cp deploy/systemd/vpnifi.service /etc/systemd/system/vpnifi.service
sudo systemctl daemon-reload
sudo systemctl enable --now vpnifi
sudo journalctl -u vpnifi -f
```

Schedule `python scripts/backup_sqlite.py` with cron or a systemd timer for the
same backup policy when not using Docker.

SQLite is suitable for one bot instance. Before running multiple instances or
requiring high availability, move to PostgreSQL and add a migration plan; do
not point multiple running instances at the same SQLite database.

## Architecture

```
Presentation Layer
        │
        ▼
Telegram Handlers
        │
        ▼
Service Layer
        │
        ▼
Repository Layer (Planned)
        │
        ▼
Database
```

## Current Progress

- ✅ Modular project structure
- ✅ User registration
- ✅ Database integration
- ✅ VPN plans
- ✅ Order creation
- ✅ Payment workflow
- ✅ Admin panel
- ✅ Tariffs, support, servers, and connection guides
- ⏳ Automatic VPN provisioning

## License

MIT License
