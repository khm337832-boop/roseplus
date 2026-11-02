"""
Goii Auto Bot — မြန်မာ/English နှစ်ဘာသာ ပံ့ပိုးတဲ့ Telegram group management bot
config.py — environment configuration
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# ---- တစ်ခုတည်း လိုအပ်တဲ့အရာ: BotFather ကနေ ရတဲ့ token ----
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "").strip()

# ---- သင့် Telegram user id (bot ပိုင်ရှင်) ----
OWNER_ID: int = int(os.getenv("OWNER_ID", "0") or 0)

# ---- Database (SQLite — အခမဲ့၊ server မလို) ----
DB_PATH: str = os.getenv("DB_PATH", str(BASE_DIR / "data" / "roseplus.db"))

# ---- Default ဘာသာစကား: my / en ----
DEFAULT_LANG: str = os.getenv("DEFAULT_LANG", "my")

# ---- Bot ရဲ့ြသမည့် နာမည် (စာတွေမှာ ဒီနာမည် ပေါ်မယ်) ----
BOT_NAME: str = os.getenv("BOT_NAME", "Goii Auto Bot")

# ---- Bot username (@mention ပြဖို့) ----
BOT_USERNAME: str = os.getenv("BOT_USERNAME", "GoiiAutoBot")

# ---- Log level ----
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

# ---- Captcha / antiflood စတဲ့ background job ရဲ့ စစ်ဆေးချိန် (စက္ကန့်) ----
JOB_INTERVAL: int = int(os.getenv("JOB_INTERVAL", "20"))

# ---- Command တစ်ခုကို တစ်ယောက်တည်း ဘယ်လောက် မြန်ဆန်စွာ ခေါ်နိုင်မလဲ (anti-flood for commands) ----
COMMAND_COOLDOWN: float = float(os.getenv("COMMAND_COOLDOWN", "0"))

# ---- Force-join (channel join မလုပ်ရင် bot ကို မသုံးနိုင်အောင်) ----
# FORCE_SUB=off  ဆိုရင် ပိတ်မယ်။ Channel ရဲ့ @username ကို ထည့်ပါ။
FORCE_SUB: str = os.getenv("FORCE_SUB", "on").strip().lower()
FORCE_SUB_CHANNEL: str = os.getenv("FORCE_SUB_CHANNEL", "@goiiautobot").strip()
FORCE_SUB_URL: str = os.getenv("FORCE_SUB_URL", "https://t.me/goiiautobot").strip()


def force_sub_enabled() -> bool:
    return FORCE_SUB not in ("off", "0", "false", "no", "")
