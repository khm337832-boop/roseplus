"""guard.py — group ထဲမှာ command တွေကို admin တွေပဲ သုံးနိုင်အောင် ကာကွယ်တယ်။

• private chat မှာ ဘယ်သူမဆို သုံးနိုင်
• group/supergroup မှာ "/command" တွေကို **admin / creator** ပဲ သုံးနိုင်
• member တွေ သုံးလို့ရတာ (public): /start /help /menu /rules /report /id /ping ...
• member တွေ ရိုးရိုးစာ ရိုက်တာကို လုံးဝ မနှောင့်ယှက်ပါ
"""
from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.dispatcher.event.bases import CancelHandler
from aiogram.types import Message

import config
import db
import i18n
from helpers import is_admin

log = logging.getLogger("goii.guard")

# member တွေ သုံးလို့ရတဲ့ command တွေ
PUBLIC_COMMANDS = {
    "start", "help", "menu", "buttons", "keyboard", "quick", "easy", "start_here",
    "rules", "report", "id", "ping", "lang", "setlang",
}


def _command_of(message: Message) -> str:
    text = (message.text or "").strip()
    if not text.startswith("/"):
        return ""
    return text.split()[0][1:].split("@")[0].lower()


class AdminOnlyCommandMiddleware:
    """group ထဲမှာ command ကို admin ပဲ သုံးနိုင်အောင်။"""

    async def __call__(self, handler, event, data):
        if not isinstance(event, Message):
            return await handler(event, data)
        if event.chat.type not in ("group", "supergroup"):
            return await handler(event, data)
        command = _command_of(event)
        if not command or command in PUBLIC_COMMANDS:
            return await handler(event, data)
        user = event.from_user
        bot: Bot | None = data.get("bot")
        if user is None or bot is None:
            return await handler(event, data)
        if config.OWNER_ID and user.id == config.OWNER_ID:
            return await handler(event, data)
        if await is_admin(bot, event.chat.id, user.id):
            return await handler(event, data)
        lang = await db.get_user_lang(user.id) or config.DEFAULT_LANG
        try:
            await event.reply(i18n.t(lang, "err_cmd_admin_only"))
        except Exception:
            pass
        log.info("guard: %s (%s) က admin မဟုတ်ဘဲ /%s သုံးခဲ့တယ်", user.id, user.full_name, command)
        raise CancelHandler()
