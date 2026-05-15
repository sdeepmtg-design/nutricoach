import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class Settings:
    bot_token: str
    bot_mode: str
    webhook_url: str | None
    webhook_secret: str | None
    port: int
    openai_api_key: str | None
    admin_ids: set[int]
    database_path: Path
    pro_month_stars: int
    pro_year_stars: int
    free_photos_per_day: int
    free_photos_per_month: int
    free_ai_messages_per_day: int
    pro_photos_per_day: int
    pro_ai_messages_per_day: int


def _parse_admin_ids(raw: str) -> set[int]:
    if not raw.strip():
        return set()
    return {int(x.strip()) for x in raw.split(",") if x.strip()}


def _bot_mode() -> str:
    mode = os.getenv("BOT_MODE", "").strip().lower()
    if mode in ("polling", "webhook"):
        return mode
    return "webhook" if os.getenv("WEBHOOK_URL") else "polling"


settings = Settings(
    bot_token=os.getenv("BOT_TOKEN", ""),
    bot_mode=_bot_mode(),
    webhook_url=os.getenv("WEBHOOK_URL") or None,
    webhook_secret=os.getenv("WEBHOOK_SECRET") or None,
    port=int(os.getenv("PORT", "10000")),
    openai_api_key=os.getenv("OPENAI_API_KEY") or None,
    admin_ids=_parse_admin_ids(os.getenv("ADMIN_IDS", "")),
    database_path=Path(os.getenv("DATABASE_PATH", "data/nutricoach.db")),
    pro_month_stars=int(os.getenv("PRO_MONTH_STARS", "150")),
    pro_year_stars=int(os.getenv("PRO_YEAR_STARS", "1200")),
    free_photos_per_day=int(os.getenv("FREE_PHOTOS_PER_DAY", "3")),
    free_photos_per_month=int(os.getenv("FREE_PHOTOS_PER_MONTH", "30")),
    free_ai_messages_per_day=int(os.getenv("FREE_AI_MESSAGES_PER_DAY", "5")),
    pro_photos_per_day=int(os.getenv("PRO_PHOTOS_PER_DAY", "50")),
    pro_ai_messages_per_day=int(os.getenv("PRO_AI_MESSAGES_PER_DAY", "100")),
)
