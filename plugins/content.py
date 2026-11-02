"""content.py — notes, filters, rules, echo"""
from __future__ import annotations

import html

from aiogram import Bot, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

import db
import i18n
from common import lang_of
from helpers import require_admin, safe

router = Router(name="content")


def _unquote(text: str) -> str:
    text = text.strip()
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'“”":
        return text[1:-1].strip()
    return text


# ------------------------------------------------------------------ notes
@router.message(Command("save", "addnote"))
async def cmd_save(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    args = (command.args or "").strip()
    if not args:
        await message.reply("/save <နာမည်>  (message ကို reply ပြန်ပြီး)")
        return
    name, _, rest = args.partition(" ")
    name = name.strip()
    content = rest.strip()
    if not content and message.reply_to_message:
        src = message.reply_to_message
        content = src.html_text or src.text or src.caption or ""
    if not content:
        await message.reply(i18n.t(lang, "note_need_content"))
        return
    await db.save_note(message.chat.id, name, content)
    await message.reply(i18n.t(lang, "note_saved", name=html.escape(name)))


@router.message(Command("get"))
async def cmd_get(message: Message, command: CommandObject) -> None:
    lang = await lang_of(message)
    name = (command.args or "").strip().split()[0] if command.args else ""
    if not name:
        await message.reply("/get <နာမည်>")
        return
    content = await db.get_note(message.chat.id, name)
    if content is None:
        await message.reply(i18n.t(lang, "note_notfound", name=html.escape(name)))
        return
    await message.reply(content, disable_web_page_preview=True)


@router.message(Command("clear"))
async def cmd_clear(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    name = (command.args or "").strip().split()[0] if command.args else ""
    if not name:
        await message.reply("/clear <နာမည်>")
        return
    await db.del_note(message.chat.id, name)
    await message.reply(i18n.t(lang, "note_deleted", name=html.escape(name)))


@router.message(Command("notes"))
async def cmd_notes(message: Message) -> None:
    lang = await lang_of(message)
    names = await db.list_notes(message.chat.id)
    if not names:
        await message.reply(i18n.t(lang, "notes_empty"))
        return
    items = "\n".join(f"• <code>#{html.escape(n)}</code>" for n in names)
    await message.reply(i18n.t(lang, "notes_list", n=len(names), items=items))


# ------------------------------------------------------------------ filters
@router.message(Command("filter"))
async def cmd_filter(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    args = (command.args or "").strip()
    trigger = ""
    reply = ""
    if args.startswith(("\"", "'", "“")):
        quote = args[0]
        end = args.find(quote, 1)
        if end > 0:
            trigger = args[1:end].strip()
            reply = args[end + 1:].strip()
    if not trigger:
        trigger, _, reply = args.partition(" ")
        trigger, reply = trigger.strip(), reply.strip()
    if not trigger:
        await message.reply("/filter <trigger> <reply>  ·  သို့ reply ပြန်ပြီး /filter <trigger>")
        return
    if not reply and message.reply_to_message:
        src = message.reply_to_message
        reply = src.html_text or src.text or src.caption or ""
    if not reply:
        await message.reply(i18n.t(lang, "note_need_content"))
        return

    admin_only = 1 if "{admin}" in reply else 0
    protect = 1 if "{protect}" in reply else 0
    reply = reply.replace("{admin}", "").replace("{protect}", "").strip()
    await db.set_filter(message.chat.id, trigger.lower(), reply, admin_only, protect)
    await message.reply(i18n.t(lang, "filter_saved", trigger=html.escape(trigger)))


@router.message(Command("stop"))
async def cmd_stop(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    trigger = _unquote(command.args or "").lower()
    if not trigger:
        await message.reply("/stop <trigger>")
        return
    if await db.get_filter(message.chat.id, trigger) is None:
        await message.reply(i18n.t(lang, "filter_notfound", trigger=html.escape(trigger)))
        return
    await db.del_filter(message.chat.id, trigger)
    await message.reply(i18n.t(lang, "filter_deleted", trigger=html.escape(trigger)))


@router.message(Command("filters"))
async def cmd_filters(message: Message) -> None:
    lang = await lang_of(message)
    filters = await db.list_filters(message.chat.id)
    if not filters:
        await message.reply(i18n.t(lang, "filters_empty"))
        return
    items = "\n".join(f"• <code>{html.escape(f['trigger'])}</code>" for f in filters[:60])
    await message.reply(i18n.t(lang, "filters_list", n=len(filters), items=items))


# ------------------------------------------------------------------ rules
@router.message(Command("setrules"))
async def cmd_setrules(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    text = (command.args or "").strip()
    if not text and message.reply_to_message:
        text = message.reply_to_message.html_text or message.reply_to_message.text or ""
    if not text:
        await message.reply("/setrules <စာသား>")
        return
    await db.update_chat(message.chat.id, rules=text)
    await message.reply(i18n.t(lang, "rules_set"))


@router.message(Command("rules"))
async def cmd_rules(message: Message, bot: Bot) -> None:
    lang = await lang_of(message)
    settings = await db.get_chat(message.chat.id)
    rules = settings.get("rules") or ""
    if not rules:
        await message.reply(i18n.t(lang, "rules_empty"))
        return
    if settings.get("rules_private"):
        try:
            await bot.send_message(message.from_user.id, f"📜 <b>{html.escape(message.chat.title or '')}</b>\n\n{rules}")
            await message.reply(i18n.t(lang, "rules_sent_pm"))
            return
        except Exception:
            pass
    await message.reply(f"📜 <b>Rules</b>\n\n{rules}", disable_web_page_preview=True)


@router.message(Command("privaterules"))
async def cmd_privaterules(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    on = (command.args or "").strip().lower() == "on"
    await db.update_chat(message.chat.id, rules_private=1 if on else 0)
    await message.reply(i18n.t(lang, "rules_private_on" if on else "rules_private_off"))


@router.message(Command("resetrules"))
async def cmd_resetrules(message: Message, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    await db.update_chat(message.chat.id, rules="")
    await message.reply(i18n.t(lang, "rules_reset"))


@router.message(Command("echo"))
async def cmd_echo(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    text = (command.args or "").strip()
    if text:
        await message.reply(text, disable_web_page_preview=True)
