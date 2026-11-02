"""helpers.py — ဘုံသုံး utility တွေ (permission, target ရှာခြင်း, lock detection, formatting)။"""
from __future__ import annotations

import asyncio
import html
import re
import time
from typing import Iterable

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.types import (
    Chat,
    ChatPermissions,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    User,
)

# ----------------------------------------------------------------- အချိန်
_TIME_RE = re.compile(r"^(\d+)\s*(s|m|h|d|w)?$", re.IGNORECASE)
_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}


def parse_time(text: str | None) -> int | None:
    """'10m', '2h', '1d', '30s', '1w' → စက္ကန့်။ မမှန်ရင် None။"""
    if not text:
        return None
    m = _TIME_RE.match(text.strip())
    if not m:
        return None
    value = int(m.group(1))
    unit = (m.group(2) or "m").lower()
    return value * _UNITS[unit]


def human_time(seconds: int) -> str:
    if seconds <= 0:
        return "0s"
    for unit, size in (("w", 604800), ("d", 86400), ("h", 3600), ("m", 60)):
        if seconds >= size and seconds % size == 0:
            return f"{seconds // size}{unit}"
    if seconds >= 3600:
        return f"{seconds // 3600}h{(seconds % 3600) // 60}m"
    if seconds >= 60:
        return f"{seconds // 60}m{seconds % 60}s"
    return f"{seconds}s"


# ----------------------------------------------------------------- user
def mention(user: User | None, fallback: str = "user") -> str:
    if user is None:
        return fallback
    name = html.escape(user.full_name or fallback)
    return f'<a href="tg://user?id={user.id}">{name}</a>'


def name_of(user: User | None, fallback: str = "user") -> str:
    if user is None:
        return fallback
    return html.escape(user.full_name or str(user.id))


# ----------------------------------------------------------------- admin
_admin_cache: dict[tuple[int, int], tuple[dict, float]] = {}
_ADMIN_TTL = 60.0


async def get_member(bot: Bot, chat_id: int, user_id: int):
    try:
        return await bot.get_chat_member(chat_id, user_id)
    except TelegramAPIError:
        return None


async def is_admin(bot: Bot, chat_id: int, user_id: int, use_cache: bool = True) -> bool:
    key = (chat_id, user_id)
    now = time.monotonic()
    if use_cache and use_cache_key(key, now):
        return _admin_cache[key][0]["is_admin"]
    member = await get_member(bot, chat_id, user_id)
    info = {"is_admin": bool(member and member.status in ("administrator", "creator")),
            "is_owner": bool(member and member.status == "creator")}
    _admin_cache[key] = (info, now + _ADMIN_TTL)
    return info["is_admin"]


def use_cache_key(key: tuple[int, int], now: float) -> bool:
    entry = _admin_cache.get(key)
    return bool(entry and entry[1] > now)


def invalidate_admin_cache(chat_id: int) -> None:
    for key in [k for k in _admin_cache if k[0] == chat_id]:
        _admin_cache.pop(key, None)


async def require_admin(bot: Bot, message: Message, lang: str, t, need: str | None = None) -> bool:
    """Admin မဖြစ်ရင် error ပြန်ပြီး False ပေးတယ်။"""
    if message.from_user is None:
        return False
    if await is_admin(bot, message.chat.id, message.from_user.id):
        return True
    await message.reply(t(lang, "err_admin_only"))
    return False


def bot_can_restrict(member) -> bool:
    return bool(getattr(member, "can_restrict_members", False))


# ----------------------------------------------------------------- target
async def extract_target(message: Message, bot: Bot, args: str) -> tuple[int | None, str | None, str]:
    """(user_id, display_name, remaining_args) ကို ပြန်ပေးတယ်။
    reply → @username → numeric id → text_mention အစဉ်လိုက် စစ်တယ်။"""
    if message.reply_to_message and message.reply_to_message.from_user:
        user = message.reply_to_message.from_user
        return user.id, user.full_name, args.strip()

    if not args:
        return None, None, ""

    # text_mention entity (ဥပမာ မမြင်ရတဲ့ user ကို tag လုပ်ထားတာ)
    for ent in message.entities or []:
        if ent.type == "text_mention" and ent.user is not None:
            return ent.user.id, ent.user.full_name, args.strip()

    parts = args.split()
    first = parts[0]
    rest = args.strip()[len(first):].strip()

    if first.startswith("@") and len(first) > 1:
        try:
            chat = await bot.get_chat(first)
            return chat.id, chat.full_name or first, rest
        except TelegramAPIError:
            return None, None, rest

    if first.lstrip("-").isdigit():
        uid = int(first)
        try:
            chat = await bot.get_chat(uid)
            return uid, chat.full_name or str(uid), rest
        except TelegramAPIError:
            return uid, str(uid), rest

    return None, None, args.strip()


# ----------------------------------------------------------------- permissions
MUTE_PERMISSIONS = ChatPermissions(can_send_messages=False)

UNMUTE_PERMISSIONS = ChatPermissions(
    can_send_messages=True,
    can_send_audios=True,
    can_send_documents=True,
    can_send_photos=True,
    can_send_videos=True,
    can_send_video_notes=True,
    can_send_voice_notes=True,
    can_send_polls=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
    can_react_to_messages=True,
)

ANTIRAID_PERMISSIONS = ChatPermissions(can_send_messages=False)


async def safe_delete(message: Message | None, bot: Bot | None = None) -> bool:
    if message is None:
        return False
    try:
        await message.delete()
        return True
    except TelegramAPIError:
        return False


async def safe(bot_method, *args, **kwargs):
    """Telegram API error တွေကို ငြိမ်ငြိမ် ဖမ်းပြီး None ပြန်ပေးတယ်။"""
    try:
        return await bot_method(*args, **kwargs)
    except TelegramAPIError:
        return None


async def kick(bot: Bot, chat_id: int, user_id: int) -> bool:
    """Kick = ban လုပ်ပြီး ချက်ချင်း unban (ပြန်ဝင်နိုင်)။"""
    try:
        await bot.ban_chat_member(chat_id, user_id)
        await bot.unban_chat_member(chat_id, user_id, only_if_banned=True)
        return True
    except TelegramBadRequest:
        return False


# ----------------------------------------------------------------- lock detection
LOCK_TYPES = [
    "url", "forward", "sticker", "gif", "photo", "video", "document", "audio",
    "voice", "video_note", "poll", "location", "contact", "game", "inline",
    "email", "phone", "spoiler", "media", "button", "mentions", "bot", "command",
]

LOCK_LABELS_MY = {
    "url": "လင့်ခ်", "forward": "Forward", "sticker": "Sticker", "gif": "GIF",
    "photo": "ဓာတ်ပုံ", "video": "ဗီဒီယို", "document": "ဖိုင်", "audio": "အသံဖိုင်",
    "voice": "Voice", "video_note": "Video note", "poll": "Poll", "location": "တည်နေရာ",
    "contact": "ဖုန်းနံပါတ် ကတ်", "game": "Game", "inline": "Inline bot",
    "email": "အီးမေးလ်", "phone": "ဖုန်းနံပါတ်", "spoiler": "Spoiler",
    "media": "မီဒီယာ (အားလုံး)", "button": "Button ပါစာ", "mentions": "Mention",
    "bot": "Bot မက်ဆေ့ချ်", "command": "Command",
}


def detect_lock_types(message: Message) -> set[str]:
    """Message ထဲမှာ ပါတဲ့ lockable content အမျိုးအစားတွေ။"""
    found: set[str] = set()
    for ent in message.entities or []:
        if ent.type == "url":
            found.add("url")
        elif ent.type == "text_link":
            found.add("url")
        elif ent.type == "email":
            found.add("email")
        elif ent.type == "phone_number":
            found.add("phone")
        elif ent.type == "mention":
            found.add("mentions")
        elif ent.type == "text_mention":
            found.add("mentions")
        elif ent.type == "bot_command":
            found.add("command")
        elif ent.type == "spoiler":
            found.add("spoiler")

    if getattr(message, "forward_origin", None) or getattr(message, "forward_date", None):
        found.add("forward")
    if message.sticker:
        found.add("sticker")
        found.add("media")
    if message.animation:
        found.add("gif")
        found.add("media")
    if message.photo:
        found.add("photo")
        found.add("media")
    if message.video:
        found.add("video")
        found.add("media")
    if message.document:
        found.add("document")
        found.add("media")
    if message.audio:
        found.add("audio")
        found.add("media")
    if message.voice:
        found.add("voice")
        found.add("media")
    if message.video_note:
        found.add("video_note")
        found.add("media")
    if message.poll:
        found.add("poll")
    if message.location or message.venue:
        found.add("location")
    if message.contact:
        found.add("contact")
    if message.game:
        found.add("game")
    if getattr(message, "via_bot", None):
        found.add("bot")
        found.add("inline")
    if message.reply_markup and isinstance(message.reply_markup, InlineKeyboardMarkup):
        if any(btn.url for row in message.reply_markup.inline_keyboard for btn in row):
            found.add("button")
    return found


def blocked_word(text: str, words: Iterable[str]) -> str | None:
    """Blocklist စကားလုံး ပါ/မပါ စစ်တယ်။ မြန်မာစာအတွက် substring, ASCII အတွက် word boundary။"""
    if not text:
        return None
    low = text.lower()
    for word in words:
        w = word.lower().strip()
        if not w:
            continue
        if w.isascii():
            if " " in w:
                if w in low:
                    return word
            elif re.search(rf"(?<!\w){re.escape(w)}(?!\w)", low):
                return word
        elif w in low:
            return word
    return None


# ----------------------------------------------------------------- welcome/filter render
def render_text(template: str, user: User | None, chat: Chat | None, count: int = 0,
                rules: str = "") -> str:
    text = template or ""
    if user is not None:
        values = {
            "{first}": html.escape(user.first_name or ""),
            "{last}": html.escape(user.last_name or ""),
            "{fullname}": html.escape(user.full_name or ""),
            "{username}": f"@{user.username}" if user.username else html.escape(user.first_name or ""),
            "{mention}": mention(user),
            "{id}": str(user.id),
        }
    else:
        values = {k: "" for k in ("{first}", "{last}", "{fullname}", "{username}", "{mention}", "{id}")}
    values["{chatname}"] = html.escape(chat.title or "") if chat else ""
    values["{count}"] = str(count)
    values["{rules}"] = rules or ""
    for k, v in values.items():
        text = text.replace(k, v)
    return text


_BUTTON_RE = re.compile(r"\[([^\]]+)\]\(buttonurl://([^)\s]+)\)")


def extract_buttons(text: str) -> tuple[str, InlineKeyboardMarkup | None]:
    """'[စာသား](buttonurl://https://…)' ကို keyboard အဖြစ် ခွဲထုတ်တယ်။"""
    if not text:
        return text, None
    rows: list[list[InlineKeyboardButton]] = []
    for label, url in _BUTTON_RE.findall(text):
        rows.append([InlineKeyboardButton(text=label, url=url)])
    if not rows:
        return text, None
    return _BUTTON_RE.sub("", text).strip(), InlineKeyboardMarkup(inline_keyboard=rows)


def add_button(markup: InlineKeyboardMarkup | None, text: str, data: str) -> InlineKeyboardMarkup:
    row = [InlineKeyboardButton(text=text, callback_data=data)]
    if markup is None:
        return InlineKeyboardMarkup(inline_keyboard=[row])
    return InlineKeyboardMarkup(inline_keyboard=[*markup.inline_keyboard, row])


async def sleep_then(seconds: float, coro_func, *args, **kwargs) -> None:
    await asyncio.sleep(seconds)
    try:
        await coro_func(*args, **kwargs)
    except Exception:  # background task — ဘယ်တော့မှ crash မဖြစ်စေ
        pass
