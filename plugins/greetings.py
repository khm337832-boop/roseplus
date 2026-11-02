"""greetings.py — welcome / goodbye / cleanwelcome / cleanservice + member join flow"""
from __future__ import annotations

from collections import defaultdict, deque

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

import db
import i18n
from common import lang_of
from helpers import (
    extract_buttons,
    render_text,
    require_admin,
    safe,
    safe_delete,
)
from plugins.antispam import antiraid_check
from plugins.captcha import send_captcha

router = Router(name="greetings")

_join_times: dict[int, deque] = defaultdict(deque)
_last_welcome: dict[int, list[int]] = defaultdict(list)


@router.message(F.new_chat_members)
async def on_join(message: Message, bot: Bot) -> None:
    settings = await db.get_chat(message.chat.id)
    lang = settings.get("lang") or "my"

    if settings.get("cleanservice"):
        await safe_delete(message, bot)

    for user in message.new_chat_members or []:
        if user.is_bot:
            continue

        # ---- AntiRaid ----
        if settings.get("antiraid"):
            if await antiraid_check(bot, message, _join_times[message.chat.id], settings):
                continue

        # ---- Welcome ----
        if settings.get("welcome_on"):
            template = settings.get("welcome") or i18n.t(lang, "default_welcome")
            count = 0
            try:
                count = await bot.get_chat_member_count(message.chat.id)
            except Exception:
                pass
            rules = settings.get("rules") or ""
            text = render_text(template, user, message.chat, count, rules)
            text, markup = extract_buttons(text)

            # cleanwelcome — အရင် welcome ကို ဖျက်
            if settings.get("cleanwelcome"):
                for mid in _last_welcome.get(message.chat.id, []):
                    await safe(bot.delete_message, message.chat.id, mid)
                _last_welcome[message.chat.id] = []

            sent = await safe(message.answer, text, reply_markup=markup,
                              disable_web_page_preview=True)
            if sent is not None:
                _last_welcome[message.chat.id].append(sent.message_id)

        # ---- CAPTCHA ----
        if settings.get("captcha"):
            await send_captcha(bot, message, user, settings)


@router.message(F.left_chat_member)
async def on_leave(message: Message, bot: Bot) -> None:
    settings = await db.get_chat(message.chat.id)
    lang = settings.get("lang") or "my"
    if settings.get("cleanservice"):
        await safe_delete(message, bot)
    user = message.left_chat_member
    if not settings.get("goodbye_on") or user is None or user.is_bot:
        return
    template = settings.get("goodbye") or i18n.t(lang, "default_goodbye")
    text = render_text(template, user, message.chat)
    text, markup = extract_buttons(text)
    await safe(message.answer, text, reply_markup=markup, disable_web_page_preview=True)


# ------------------------------------------------------------------ welcome commands
@router.message(Command("setwelcome"))
async def cmd_setwelcome(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    text = (command.args or "").strip()
    if not text and message.reply_to_message:
        text = message.reply_to_message.html_text or message.reply_to_message.text or ""
    if not text:
        await message.reply(i18n.t(lang, "welcome_vars"))
        return
    await db.update_chat(message.chat.id, welcome=text, welcome_on=1)
    await message.reply(i18n.t(lang, "welcome_set") + "\n" + i18n.t(lang, "welcome_vars"))


@router.message(Command("welcome"))
async def cmd_welcome(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    arg = (command.args or "").strip().lower()
    settings = await db.get_chat(message.chat.id)
    if arg == "on":
        await db.update_chat(message.chat.id, welcome_on=1)
        await message.reply(i18n.t(lang, "welcome_on"))
    elif arg == "off":
        await db.update_chat(message.chat.id, welcome_on=0)
        await message.reply(i18n.t(lang, "welcome_off"))
    else:
        text = settings.get("welcome") or i18n.t(lang, "default_welcome")
        await message.reply(i18n.t(lang, "welcome_show", text=text),
                            disable_web_page_preview=True)


@router.message(Command("resetwelcome"))
async def cmd_resetwelcome(message: Message, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    await db.update_chat(message.chat.id, welcome="")
    await message.reply(i18n.t(lang, "welcome_reset"))


@router.message(Command("setgoodbye"))
async def cmd_setgoodbye(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    text = (command.args or "").strip()
    if not text and message.reply_to_message:
        text = message.reply_to_message.html_text or message.reply_to_message.text or ""
    if not text:
        await message.reply(i18n.t(lang, "welcome_vars"))
        return
    await db.update_chat(message.chat.id, goodbye=text, goodbye_on=1)
    await message.reply(i18n.t(lang, "goodbye_set"))


@router.message(Command("goodbye"))
async def cmd_goodbye(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    arg = (command.args or "").strip().lower()
    if arg == "on":
        await db.update_chat(message.chat.id, goodbye_on=1)
        await message.reply(i18n.t(lang, "goodbye_on"))
    elif arg == "off":
        await db.update_chat(message.chat.id, goodbye_on=0)
        await message.reply(i18n.t(lang, "goodbye_off"))
    else:
        settings = await db.get_chat(message.chat.id)
        await message.reply(i18n.t(lang, "welcome_show",
                                   text=settings.get("goodbye") or i18n.t(lang, "default_goodbye")))
        return


@router.message(Command("resetgoodbye"))
async def cmd_resetgoodbye(message: Message, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    await db.update_chat(message.chat.id, goodbye="")
    await message.reply(i18n.t(lang, "goodbye_reset"))


@router.message(Command("cleanwelcome"))
async def cmd_cleanwelcome(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    on = (command.args or "").strip().lower() == "on"
    await db.update_chat(message.chat.id, cleanwelcome=1 if on else 0)
    await message.reply(i18n.t(lang, "cleanwelcome_on" if on else "cleanwelcome_off"))


@router.message(Command("cleanservice"))
async def cmd_cleanservice(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    on = (command.args or "").strip().lower() == "on"
    await db.update_chat(message.chat.id, cleanservice=1 if on else 0)
    await message.reply(i18n.t(lang, "cleanservice_on" if on else "cleanservice_off"))
