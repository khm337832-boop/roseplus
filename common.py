"""common.py — handler တွေ အားလုံး သုံးတဲ့ ဘုံ function တွေ။"""
from __future__ import annotations

from aiogram import Bot
from aiogram.types import Message

import db
from config import DEFAULT_LANG
from helpers import safe


async def chat_lang(chat_id: int) -> str:
    settings = await db.get_chat(chat_id)
    return settings.get("lang") or DEFAULT_LANG


async def lang_of(message: Message) -> str:
    return await chat_lang(message.chat.id)


async def log_action(bot: Bot, chat_id: int, text: str) -> None:
    settings = await db.get_chat(chat_id)
    channel = settings.get("log_channel") or 0
    if channel:
        await safe(bot.send_message, channel, text, disable_web_page_preview=True)


async def is_trusted(chat_id: int, user_id: int) -> bool:
    return await db.is_approved(chat_id, user_id)
