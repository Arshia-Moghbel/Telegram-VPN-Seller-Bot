from dataclasses import dataclass
import os

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_id: int
    database_url: str
    log_level: str
    payment_card: str
    card_owner: str
    support_username: str
    instance_lock_path: str
    log_file: str


settings = Settings(
    bot_token=os.getenv("BOT_TOKEN", ""),
    # Never fall back to a real Telegram account.  A missing ADMIN_ID must stop
    # the bot instead of granting that account access to a new deployment.
    admin_id=int(os.getenv("ADMIN_ID") or "0"),
    database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///vpnifi.db"),
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    payment_card=os.getenv("PAYMENT_CARD", ""),
    card_owner=os.getenv("CARD_OWNER", ""),
    support_username=os.getenv("SUPPORT_USERNAME", ""),
    instance_lock_path=os.getenv("INSTANCE_LOCK_PATH", ".vpnifi.lock"),
    log_file=os.getenv("LOG_FILE", ""),
)


def validate_settings() -> None:
    """Fail fast for the two credentials required to operate the bot safely."""
    missing = []
    if not settings.bot_token:
        missing.append("BOT_TOKEN")
    if settings.admin_id <= 0:
        missing.append("ADMIN_ID")
    if missing:
        raise RuntimeError(
            "Missing or invalid required environment variable(s): " + ", ".join(missing)
        )
