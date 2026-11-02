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

# member တွေ သုံးလို့ရတဲ့ command တွေ — group ထဲမှာ default က "ဘာမှ မရ" ပါ
PUBLIC_COMMANDS: set[str] = set()

# True ဆိုရင် group ထဲမှာ member တွေ command ရိုက်ရင် bot က **လုံးဝ ဆိတ်ဆိတ်** နေမယ်
MEMBERS_SILENT = True


async def _is_admin_safe(bot, message: Message) -> bool:
    user = message.from_user
    if bot is None or user is None:
        return False
    if config.OWNER_ID and user.id == config.OWNER_ID:
        return True
    return await is_admin(bot, message.chat.id, user.id)


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
        from plugins.menu import is_menu_text

        if not command:
            # keyboard button စာသား ဆိုရင် member အတွက် ဆိတ်ဆိတ်ထား
            if is_menu_text(event.text) and not await _is_admin_safe(data.get("bot"), event):
                raise CancelHandler()
            return await handler(event, data)
        if command in PUBLIC_COMMANDS:
            return await handler(event, data)
        user = event.from_user
        bot: Bot | None = data.get("bot")
        if user is None or bot is None:
            return await handler(event, data)
        if config.OWNER_ID and user.id == config.OWNER_ID:
            return await handler(event, data)
        if await is_admin(bot, event.chat.id, user.id):
            return await handler(event, data)
        log.info("guard: %s (%s) က admin မဟုတ်ဘဲ /%s သုံးခဲ့တယ် — ဆိတ်ဆိတ်နေမယ်",
                 user.id, user.full_name, command)
        # member တွေဆီ ဘာမှ မပြောဘဲ ပိတ်လိုက်တယ်
        raise CancelHandler()
