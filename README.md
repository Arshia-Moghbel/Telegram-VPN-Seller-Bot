# Vpnifi - Telegram VPN Seller Bot

A production-oriented Telegram bot for selling and managing VPN subscriptions, built with Python and aiogram.
Address: @Vpnifi26_bot

> **Status:** 🚧 In Active Development

## Overview

Vpnifi is a modular Telegram bot for selling and managing VPN subscriptions. The project is being developed with production-quality architecture in mind, making it suitable both as a real commercial service and as a portfolio project.

The long-term goal is to provide automatic VPN provisioning, payment processing, subscription management, and an extensible administration panel.

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

- Python 3.13
- aiogram 3
- SQLAlchemy 2
- SQLite (development)
- PostgreSQL (planned)
- Git & GitHub

## Project Structure

```text
Vpnifi26_bot/
├── handlers/
├── services/
├── database/
├── keyboards/
├── states/
├── models/
├── utils/
├── logs/
├── main.py
└── config.py
```

## Roadmap

### Version 0.1
- [x] Project structure
- [x] User registration
- [x] Database
- [x] Plans
- [x] Order model

### Version 0.2
- [ ] Payment workflow
- [ ] Receipt upload
- [ ] Admin panel
- [ ] Order management

### Version 0.3
- [ ] PostgreSQL
- [ ] Alembic
- [ ] Docker
- [ ] Logging

### Version 1.0
- [ ] Automatic VPN provisioning
- [ ] Multiple VPN servers
- [ ] Production deployment

## Development

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

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
