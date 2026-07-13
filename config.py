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


settings = Settings(
    bot_token=os.getenv("BOT_TOKEN", ""),
    admin_id=int(os.getenv("ADMIN_ID") or "7311139872"),
    database_url=os.getenv("DATABASE_URL", "sqlite+aiosqlite:///vpnifi.db"),
    log_level=os.getenv("LOG_LEVEL", "INFO"),
    payment_card=os.getenv("PAYMENT_CARD", ""),
    card_owner=os.getenv("CARD_OWNER", ""),
    support_username=os.getenv("SUPPORT_USERNAME", ""),
)
