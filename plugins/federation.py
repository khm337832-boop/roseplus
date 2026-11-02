"""federation.py — group အများအပြားကို ပေါင်းပြီး ban တစ်ခါနဲ့ အားလုံးမှာ ban ဖြစ်စေခြင်း"""
from __future__ import annotations

import html
import secrets

from aiogram import Bot, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import Message

import db
import i18n
from common import lang_of
from helpers import extract_target, name_of, require_admin, safe

router = Router(name="federation")


@router.message(Command("newfed"))
async def cmd_newfed(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    name = (command.args or "").strip()
    if not name:
        await message.reply("/newfed <အမည်>")
        return
    if await db.fed_by_name(name):
        await message.reply(i18n.t(lang, "fed_exists"))
        return
    fed_id = secrets.token_hex(4)
    await db.create_fed(fed_id, name, message.from_user.id)
    await message.reply(i18n.t(lang, "fed_created", name=html.escape(name), fed_id=fed_id))


@router.message(Command("fedinfo"))
async def cmd_fedinfo(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    arg = (command.args or "").strip()
    fed = None
    if arg:
        fed = await db.get_fed(arg) or await db.fed_by_name(arg)
    else:
        fed = await db.chat_fed(message.chat.id)
    if not fed:
        await message.reply(i18n.t(lang, "fed_not_found"))
        return
    chats = await db.fed_chats_list(fed["fed_id"])
    bans = await db.fed_ban_list(fed["fed_id"])
    await message.reply(i18n.t(
        lang, "fed_info", name=html.escape(fed["name"]), fed_id=fed["fed_id"],
        owner=fed["owner_id"], chats=len(chats), bans=len(bans)))


@router.message(Command("joinfed"))
async def cmd_joinfed(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    fed_id = (command.args or "").strip()
    fed = await db.get_fed(fed_id)
    if not fed:
        await message.reply(i18n.t(lang, "fed_not_found"))
        return
    await db.join_fed(message.chat.id, fed_id)
    await message.reply(i18n.t(lang, "fed_joined", name=html.escape(fed["name"])))


@router.message(Command("leavefed"))
async def cmd_leavefed(message: Message, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    await db.leave_fed(message.chat.id)
    await message.reply(i18n.t(lang, "fed_left"))


@router.message(Command("fban"))
async def cmd_fban(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    fed = await db.chat_fed(message.chat.id)
    if not fed:
        await message.reply(i18n.t(lang, "fed_not_found"))
        return
    uid, name, reason = await extract_target(message, bot, command.args or "")
    if uid is None:
        await message.reply(i18n.t(lang, "err_need_target"))
        return
    await db.fed_ban(fed["fed_id"], uid, reason or "—", message.from_user.id)
    count = 0
    for chat_id in await db.fed_chats_list(fed["fed_id"]):
        if await safe(bot.ban_chat_member, chat_id, uid) is not None:
            count += 1
    await message.reply(i18n.t(lang, "fban_done", user=html.escape(name or str(uid)), n=count))


@router.message(Command("funban"))
async def cmd_funban(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    fed = await db.chat_fed(message.chat.id)
    if not fed:
        await message.reply(i18n.t(lang, "fed_not_found"))
        return
    uid, name, _reason = await extract_target(message, bot, command.args or "")
    if uid is None:
        await message.reply(i18n.t(lang, "err_need_target"))
        return
    await db.fed_unban(fed["fed_id"], uid)
    for chat_id in await db.fed_chats_list(fed["fed_id"]):
        await safe(bot.unban_chat_member, chat_id, uid, only_if_banned=True)
    await message.reply(i18n.t(lang, "funban_done", user=html.escape(name or str(uid))))


@router.message(Command("fbanlist"))
async def cmd_fbanlist(message: Message, bot: Bot) -> None:
    lang = await lang_of(message)
    fed = await db.chat_fed(message.chat.id)
    if not fed:
        await message.reply(i18n.t(lang, "fed_not_found"))
        return
    bans = await db.fed_ban_list(fed["fed_id"])
    if not bans:
        await message.reply(i18n.t(lang, "fban_none"))
        return
    items = "\n".join(
        f"• <code>{b['user_id']}</code> — {html.escape(b['reason'] or '—')}" for b in bans[:40]
    )
    await message.reply(i18n.t(lang, "fban_list", n=len(bans), items=items))
