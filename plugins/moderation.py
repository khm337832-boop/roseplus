"""moderation.py — ban/kick/mute/warn/purge/pin/report/promote"""
from __future__ import annotations

import html
from datetime import timedelta

from aiogram import Bot, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import ChatMemberAdministrator, ChatMemberOwner, Message

import db
import i18n
from common import lang_of, log_action
from helpers import (
    MUTE_PERMISSIONS,
    UNMUTE_PERMISSIONS,
    extract_target,
    get_member,
    human_time,
    is_admin,
    kick,
    mention,
    name_of,
    parse_time,
    require_admin,
    safe,
    safe_delete,
)

router = Router(name="moderation")


def _group_only(message: Message) -> bool:
    return message.chat.type in ("group", "supergroup")


async def _resolve(message: Message, command: CommandObject, bot: Bot):
    """(lang, user_id, name, rest) — admin မဟုတ်ရင် (lang, None, None, None)"""
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return lang, None, None, None
    uid, name, rest = await extract_target(message, bot, command.args or "")
    if uid is None:
        await message.reply(i18n.t(lang, "err_need_target"))
        return lang, None, None, None
    if message.from_user and uid == message.from_user.id:
        await message.reply(i18n.t(lang, "err_generic"))
        return lang, None, None, None
    if await is_admin(bot, message.chat.id, uid):
        await message.reply(i18n.t(lang, "target_is_admin"))
        return lang, None, None, None
    return lang, uid, name, rest


# ------------------------------------------------------------------ ban family
@router.message(Command("ban", "tban", "kick"))
async def cmd_ban(message: Message, command: CommandObject, bot: Bot) -> None:
    lang, uid, name, rest = await _resolve(message, command, bot)
    if uid is None:
        return
    user_html = html.escape(name or str(uid))
    until = None
    if command.command == "tban":
        seconds = parse_time((rest or "").split()[0] if rest else None)
        if not seconds:
            await message.reply(i18n.t(lang, "err_bad_time"))
            return
        until = timedelta(seconds=seconds)

    if command.command == "kick":
        ok = await kick(bot, message.chat.id, uid)
        if ok:
            await message.reply(i18n.t(lang, "kick_done", user=user_html))
            await log_action(bot, message.chat.id, i18n.t(
                lang, "log_kick", user=user_html, uid=uid,
                admin=name_of(message.from_user)))
        else:
            await message.reply(i18n.t(lang, "err_generic"))
        return

    if until:
        result = await safe(bot.ban_chat_member, message.chat.id, uid, until_date=until)
    else:
        result = await safe(bot.ban_chat_member, message.chat.id, uid)
    if result is None:
        await message.reply(i18n.t(lang, "err_generic"))
        return
    if until:
        await message.reply(i18n.t(lang, "ban_done_time", user=user_html,
                                   time=human_time(int(until.total_seconds()))))
    else:
        await message.reply(i18n.t(lang, "ban_done", user=user_html))
    await log_action(bot, message.chat.id, i18n.t(
        lang, "log_ban", user=user_html, uid=uid, admin=name_of(message.from_user),
        reason=(rest or "—")))


@router.message(Command("unban"))
async def cmd_unban(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    uid, name, _rest = await extract_target(message, bot, command.args or "")
    if uid is None:
        await message.reply(i18n.t(lang, "err_need_target"))
        return
    result = await safe(bot.unban_chat_member, message.chat.id, uid, only_if_banned=True)
    if result is None:
        await message.reply(i18n.t(lang, "err_generic"))
        return
    await message.reply(i18n.t(lang, "unban_done", user=html.escape(name or str(uid))))


# ------------------------------------------------------------------ mute family
@router.message(Command("mute", "tmute"))
async def cmd_mute(message: Message, command: CommandObject, bot: Bot) -> None:
    lang, uid, name, rest = await _resolve(message, command, bot)
    if uid is None:
        return
    until = None
    if command.command == "tmute":
        seconds = parse_time((rest or "").split()[0] if rest else None)
        if not seconds:
            await message.reply(i18n.t(lang, "err_bad_time"))
            return
        until = timedelta(seconds=seconds)
    result = await safe(bot.restrict_chat_member, message.chat.id, uid,
                        permissions=MUTE_PERMISSIONS, until_date=until)
    if result is None:
        await message.reply(i18n.t(lang, "err_generic"))
        return
    user_html = html.escape(name or str(uid))
    if until:
        await message.reply(i18n.t(lang, "mute_done_time", user=user_html,
                                   time=human_time(int(until.total_seconds()))))
    else:
        await message.reply(i18n.t(lang, "mute_done", user=user_html))
    await log_action(bot, message.chat.id, i18n.t(
        lang, "log_mute", user=user_html, uid=uid, admin=name_of(message.from_user),
        time=human_time(int(until.total_seconds())) if until else "∞"))


@router.message(Command("unmute"))
async def cmd_unmute(message: Message, command: CommandObject, bot: Bot) -> None:
    lang, uid, name, _rest = await _resolve(message, command, bot)
    if uid is None:
        return
    result = await safe(bot.restrict_chat_member, message.chat.id, uid,
                        permissions=UNMUTE_PERMISSIONS)
    if result is None:
        await message.reply(i18n.t(lang, "err_generic"))
        return
    await message.reply(i18n.t(lang, "unmute_done"))


# ------------------------------------------------------------------ warns
async def apply_warn_punishment(bot: Bot, chat_id: int, uid: int, mode: str) -> str:
    mode = (mode or "ban").lower()
    if mode == "kick":
        await kick(bot, chat_id, uid)
        return "kick"
    if mode == "mute":
        await safe(bot.restrict_chat_member, chat_id, uid, permissions=MUTE_PERMISSIONS)
        return "mute"
    if mode == "tmute":
        await safe(bot.restrict_chat_member, chat_id, uid, permissions=MUTE_PERMISSIONS,
                   until_date=timedelta(hours=1))
        return "tmute 1h"
    if mode == "tban":
        await safe(bot.ban_chat_member, chat_id, uid, until_date=timedelta(days=1))
        return "tban 1d"
    await safe(bot.ban_chat_member, chat_id, uid)
    return "ban"


@router.message(Command("warn"))
async def cmd_warn(message: Message, command: CommandObject, bot: Bot) -> None:
    lang, uid, name, rest = await _resolve(message, command, bot)
    if uid is None:
        return
    settings = await db.get_chat(message.chat.id)
    limit = settings.get("warn_limit", 3)
    count = await db.add_warn(message.chat.id, uid, rest or "—", settings.get("warn_expiry", 0))
    user_html = html.escape(name or str(uid))
    if count >= limit:
        action = await apply_warn_punishment(bot, message.chat.id, uid, settings.get("warn_mode", "ban"))
        await db.reset_warns(message.chat.id, uid)
        await message.reply(i18n.t(lang, "warn_limit_reached", user=user_html, limit=limit, action=action))
    else:
        text = i18n.t(lang, "warn_done", user=user_html, count=count, limit=limit)
        if rest:
            text += "\n" + i18n.t(lang, "warn_reason", reason=html.escape(rest))
        await message.reply(text)
    await log_action(bot, message.chat.id, i18n.t(
        lang, "log_warn", user=user_html, uid=uid, admin=name_of(message.from_user),
        count=count, limit=limit, reason=(rest or "—")))


@router.message(Command("unwarn", "rmwarn"))
async def cmd_unwarn(message: Message, command: CommandObject, bot: Bot) -> None:
    lang, uid, name, _rest = await _resolve(message, command, bot)
    if uid is None:
        return
    count = await db.remove_warn(message.chat.id, uid)
    await message.reply(i18n.t(lang, "unwarn_done", count=count))


@router.message(Command("warns"))
async def cmd_warns(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    uid, name, _rest = await extract_target(message, bot, command.args or "")
    if uid is None and message.from_user:
        uid, name = message.from_user.id, message.from_user.full_name
    if uid is None:
        await message.reply(i18n.t(lang, "err_need_target"))
        return
    settings = await db.get_chat(message.chat.id)
    count, reasons = await db.get_warn(message.chat.id, uid)
    if count == 0:
        await message.reply(i18n.t(lang, "warns_none", user=html.escape(name or str(uid))))
        return
    reason_text = "\n".join(f"{i+1}. {html.escape(r)}" for i, r in enumerate(reasons))
    await message.reply(i18n.t(lang, "warns_list", user=html.escape(name or str(uid)),
                               count=count, limit=settings.get("warn_limit", 3),
                               reasons=reason_text))


@router.message(Command("resetwarns"))
async def cmd_resetwarns(message: Message, command: CommandObject, bot: Bot) -> None:
    lang, uid, name, _rest = await _resolve(message, command, bot)
    if uid is None:
        return
    await db.reset_warns(message.chat.id, uid)
    await message.reply(i18n.t(lang, "warns_reset", user=html.escape(name or str(uid))))


@router.message(Command("setwarnlimit"))
async def cmd_setwarnlimit(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    arg = (command.args or "").strip()
    if not arg.isdigit() or int(arg) < 1:
        await message.reply("/setwarnlimit 3")
        return
    await db.update_chat(message.chat.id, warn_limit=int(arg))
    await message.reply(i18n.t(lang, "warn_limit_set", n=int(arg)))


@router.message(Command("setwarnmode"))
async def cmd_setwarnmode(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    mode = (command.args or "").strip().lower()
    if mode not in ("ban", "kick", "mute", "tban", "tmute"):
        await message.reply("/setwarnmode ban|kick|mute|tban|tmute")
        return
    await db.update_chat(message.chat.id, warn_mode=mode)
    await message.reply(i18n.t(lang, "warn_mode_set", mode=mode))


# ------------------------------------------------------------------ purge / delete / pin
@router.message(Command("purge"))
async def cmd_purge(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    if not message.reply_to_message:
        await message.reply(i18n.t(lang, "purge_need_reply"))
        return
    start_id = message.reply_to_message.message_id
    end_id = message.message_id
    deleted = 0
    ids = list(range(start_id, end_id + 1))
    for i in range(0, len(ids), 100):
        chunk = ids[i:i + 100]
        try:
            await bot.delete_messages(message.chat.id, chunk)
            deleted += len(chunk)
        except Exception:
            for mid in chunk:
                try:
                    await bot.delete_message(message.chat.id, mid)
                    deleted += 1
                except Exception:
                    pass
    note = await message.answer(i18n.t(lang, "purge_done", n=deleted))
    await safe_delete(note, bot)


@router.message(Command("del"))
async def cmd_del(message: Message, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    target = message.reply_to_message or message
    if await safe_delete(target, bot):
        await safe_delete(message, bot)
        if target is message:
            await message.answer(i18n.t(lang, "del_done"))


@router.message(Command("pin"))
async def cmd_pin(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    if not message.reply_to_message:
        await message.reply(i18n.t(lang, "pin_need_reply"))
        return
    notify = (command.args or "").strip().lower() in ("loud", "notify")
    await safe(bot.pin_chat_message, message.chat.id, message.reply_to_message.message_id,
               disable_notification=not notify)
    await message.reply(i18n.t(lang, "pin_done"))


@router.message(Command("unpin"))
async def cmd_unpin(message: Message, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    await safe(bot.unpin_chat_message, message.chat.id)
    await message.reply(i18n.t(lang, "unpin_done"))


@router.message(Command("permapin"))
async def cmd_permapin(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    text = (command.args or "").strip()
    if not text:
        await message.reply("/permapin <text>")
        return
    sent = await message.answer(text, disable_web_page_preview=True)
    await safe(bot.pin_chat_message, message.chat.id, sent.message_id, disable_notification=True)


# ------------------------------------------------------------------ report / approvals
@router.message(Command("report"))
async def cmd_report(message: Message, bot: Bot) -> None:
    lang = await lang_of(message)
    admins = []
    try:
        async for member in bot.get_chat_administrators(message.chat.id):
            if member.user and not member.user.is_bot:
                admins.append(mention(member.user))
    except Exception:
        pass
    text = i18n.t(lang, "report_sent")
    if admins:
        text += "\n" + " ".join(admins[:6])
    if message.reply_to_message:
        text += f"\n\n🔗 {message.reply_to_message.get_url() or ''}"
    await message.reply(text, disable_web_page_preview=True)


@router.message(Command("approve"))
async def cmd_approve(message: Message, command: CommandObject, bot: Bot) -> None:
    lang, uid, name, _rest = await _resolve(message, command, bot)
    if uid is None:
        return
    await db.approve(message.chat.id, uid)
    await message.reply(i18n.t(lang, "approved", user=html.escape(name or str(uid))))


@router.message(Command("unapprove"))
async def cmd_unapprove(message: Message, command: CommandObject, bot: Bot) -> None:
    lang, uid, name, _rest = await _resolve(message, command, bot)
    if uid is None:
        return
    await db.unapprove(message.chat.id, uid)
    await message.reply(i18n.t(lang, "unapproved", user=html.escape(name or str(uid))))


@router.message(Command("approved"))
async def cmd_approved_list(message: Message, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    users = await db.list_approved(message.chat.id)
    if not users:
        await message.reply(i18n.t(lang, "approved_empty"))
        return
    await message.reply(i18n.t(lang, "approved_list",
                               users="\n".join(f"• <code>{u}</code>" for u in users[:50])))


# ------------------------------------------------------------------ promote / demote / adminlist
@router.message(Command("promote"))
async def cmd_promote(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    uid, name, _rest = await extract_target(message, bot, command.args or "")
    if uid is None:
        await message.reply(i18n.t(lang, "err_need_target"))
        return
    try:
        await bot.promote_chat_member(
            message.chat.id, uid,
            can_delete_messages=True, can_restrict_members=True,
            can_pin_messages=True, can_invite_users=True, can_manage_video_chats=True,
        )
    except Exception:
        await message.reply(i18n.t(lang, "err_generic"))
        return
    await message.reply(i18n.t(lang, "promote_done", user=html.escape(name or str(uid))))


@router.message(Command("demote"))
async def cmd_demote(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    uid, name, _rest = await extract_target(message, bot, command.args or "")
    if uid is None:
        await message.reply(i18n.t(lang, "err_need_target"))
        return
    try:
        await bot.promote_chat_member(
            message.chat.id, uid,
            can_delete_messages=False, can_restrict_members=False,
            can_pin_messages=False, can_invite_users=False, can_manage_video_chats=False,
            can_change_info=False, can_promote_members=False,
        )
    except Exception:
        await message.reply(i18n.t(lang, "err_generic"))
        return
    await message.reply(i18n.t(lang, "demote_done", user=html.escape(name or str(uid))))


@router.message(Command("adminlist"))
async def cmd_adminlist(message: Message, bot: Bot) -> None:
    lang = await lang_of(message)
    lines = []
    try:
        async for member in bot.get_chat_administrators(message.chat.id):
            if member.user:
                tag = "👑" if isinstance(member, ChatMemberOwner) else "•"
                lines.append(f"{tag} {mention(member.user)}")
    except Exception:
        pass
    if not lines:
        await message.reply("—")
        return
    await message.reply(i18n.t(lang, "admin_list", users="\n".join(lines)))


@router.message(Command("admincache"))
async def cmd_admincache(message: Message, bot: Bot) -> None:
    from helpers import invalidate_admin_cache

    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    invalidate_admin_cache(message.chat.id)
    await message.reply(i18n.t(lang, "admin_cache_cleared"))
