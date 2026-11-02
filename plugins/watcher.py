"""watcher.py — group ထဲ ဝင်လာတဲ့ message တိုင်းကို ဖြတ်စစ်တဲ့ engine
locks → blocklist → antiflood → filters → #notes အစဉ်လိုက်
"""
from __future__ import annotations

import html
import json
import re

from aiogram import Bot, F, Router
from aiogram.types import Message

import db
import i18n
from common import log_action
from helpers import (
    blocked_word,
    detect_lock_types,
    is_admin,
    mention,
    name_of,
    safe,
)
from plugins.antispam import apply_mode, flood_register

router = Router(name="watcher")


def match_trigger(text: str, trigger: str) -> bool:
    """Filter trigger ကို message ထဲမှာ ရှာ (ASCII ဆို word boundary, မြန်မာဆို substring)။"""
    low = text.lower()
    t = trigger.lower().strip()
    if not t:
        return False
    if t.isascii():
        if " " in t:
            return t in low
        return re.search(rf"(?<!\w){re.escape(t)}(?!\w)", low) is not None
    return t in low


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def watch(message: Message, bot: Bot) -> None:
    # service message တွေကို ကျော်
    if (message.new_chat_members or message.left_chat_member
            or message.pinned_message or message.group_chat_created):
        return
    if message.from_user is None or message.from_user.is_bot:
        return

    chat_id = message.chat.id
    settings = await db.get_chat(chat_id)
    lang = settings.get("lang") or "my"
    uid = message.from_user.id

    await db.bump_messages(chat_id)

    text = message.text or message.caption or ""

    # ---- command တွေကို ဒီမှာ မကိုင်ပါ (handler သီးသန့် ရှိတယ်)
    if text.startswith("/"):
        return

    # ---- admin / trusted တွေ ကင်းလွတ်
    if await is_admin(bot, chat_id, uid) or await db.is_approved(chat_id, uid):
        return

    # ---- 1) Locks
    locks = set(json.loads(settings.get("locks") or "[]"))
    if locks:
        violated = detect_lock_types(message) & locks
        if violated:
            await safe(message.delete)
            kind = sorted(violated)[0]
            from helpers import LOCK_LABELS_MY

            label = LOCK_LABELS_MY.get(kind, kind) if lang == "my" else kind
            warning = await safe(message.answer, i18n.t(
                lang, "lock_violation", user=mention(message.from_user), type=label))
            if warning is not None:
                from helpers import safe_delete

                await safe_delete(warning, bot)
            await log_action(bot, chat_id, i18n.t(
                lang, "log_lock", user=html.escape(message.from_user.full_name),
                uid=uid, type=label))
            return

    # ---- 2) Blocklist
    if text:
        words = await db.list_blocks(chat_id)
        if words:
            hit = blocked_word(text, words)
            if hit:
                await safe(message.delete)
                mode = settings.get("blocklist_mode") or "delete"
                action = await apply_mode(bot, message, uid, mode, lang, "blocklist", reason=hit)
                if mode != "delete":
                    note = await safe(message.answer, "🚫 " + i18n.t(
                        lang, "block_added", word=html.escape(hit)))
                    if note is not None:
                        from helpers import safe_delete

                        await safe_delete(note, bot)
                await log_action(bot, chat_id, i18n.t(
                    lang, "log_blocklist", user=html.escape(message.from_user.full_name),
                    uid=uid, word=html.escape(hit), action=action))
                return

    # ---- 3) Antiflood
    triggered, ids = flood_register(chat_id, uid, message.message_id, settings)
    if triggered:
        for mid in ids:
            await safe(bot.delete_message, chat_id, mid)
        action = await apply_mode(bot, message, uid, settings.get("flood_mode") or "mute",
                                  lang, "antiflood")
        await log_action(bot, chat_id, i18n.t(
            lang, "log_flood", user=html.escape(message.from_user.full_name),
            uid=uid, action=action))
        return

    # ---- 4) Filters
    if text:
        for f in await db.list_filters(chat_id):
            if not match_trigger(text, f["trigger"]):
                continue
            if f["admin_only"] and not await is_admin(bot, chat_id, uid):
                continue
            await safe(message.reply, f["reply"], disable_web_page_preview=True)
            return

    # ---- 5) #note
    if text.startswith("#") and len(text) > 1:
        note_name = text.split()[0][1:]
        content = await db.get_note(chat_id, note_name)
        if content:
            await safe(message.reply, content, disable_web_page_preview=True)
