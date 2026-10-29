

# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and follows Semantic Versioning.

## [Unreleased]

### Added
- Planned payment workflow
- Planned admin panel
- Alembic schema tracking and a PostgreSQL production Compose profile
- Rotating application logs configurable through `LOG_FILE`
- Multi-server inventory with capacity-aware selection for approved orders
- A provisioning workflow ready to connect to a future VPN panel API

## [0.1.0] - 2026-07-11

### Added
- Initial project structure
- Telegram bot setup with aiogram 3
- SQLAlchemy database integration
- User model
- Plan model
- Order model
- Order service
- Dynamic VPN plans
- Project README
- MIT License
- GitHub project configuration files

### Changed
- Replaced simple configuration with Settings class
- Improved repository structure
- Enhanced documentation

### Fixed
- Telegram bot token loading
- Database initialization issues
