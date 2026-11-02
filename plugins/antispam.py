"""antispam.py — locks, blocklist, antiflood, antiraid (command တွေ + engine)"""
from __future__ import annotations

import asyncio
import html
import json
import time
from collections import defaultdict, deque
from datetime import timedelta

from aiogram import Bot, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import ChatPermissions, Message

import db
import i18n
from common import lang_of, log_action
from helpers import (
    LOCK_LABELS_MY,
    LOCK_TYPES,
    MUTE_PERMISSIONS,
    human_time,
    kick,
    name_of,
    parse_time,
    require_admin,
    safe,
)

router = Router(name="antispam")

# ------------------------------------------------------------------ state
_consecutive: dict[int, dict] = {}
_window: dict[tuple[int, int], deque] = defaultdict(deque)


def flood_register(chat_id: int, user_id: int, message_id: int, settings: dict) -> tuple[bool, list[int]]:
    """(triggered, ဖျက်ရမယ့် message id တွေ) ကို ပြန်ပေးတယ်။"""
    limit = int(settings.get("flood") or 0)
    win = int(settings.get("flood_win") or 0)
    win_sec = int(settings.get("flood_win_seconds") or 10)
    state = _consecutive.setdefault(chat_id, {"last_user": 0, "count": 0})
    if state["last_user"] != user_id:
        state["last_user"] = user_id
        state["count"] = 0
    state["count"] += 1

    q = _window[(chat_id, user_id)]
    now = time.monotonic()
    q.append((now, message_id))
    while q and now - q[0][0] > max(win_sec, 1):
        q.popleft()

    triggered = bool(limit and state["count"] >= limit) or bool(win and len(q) >= win)
    if not triggered:
        return False, []
    ids = [mid for _ts, mid in q] if settings.get("clearflood") else [message_id]
    state["count"] = 0
    q.clear()
    return True, ids


async def apply_mode(bot: Bot, message: Message, user_id: int, mode: str,
                     lang: str, action_log: str, reason: str = "") -> str:
    """blocklist / flood တို့အတွက် punishment အလုပ်လုပ်တယ်။ လုပ်ခဲ့တဲ့ action ကို ပြန်ပေးတယ်။"""
    chat_id = message.chat.id
    mode = (mode or "delete").lower()
    parts = mode.split()
    kind = parts[0]
    duration = parse_time(parts[1]) if len(parts) > 1 else None

    if kind in ("delete", "del"):
        return "delete"
    if kind == "warn":
        settings = await db.get_chat(chat_id)
        limit = settings.get("warn_limit", 3)
        count = await db.add_warn(chat_id, user_id, reason or "antispam", settings.get("warn_expiry", 0))
        if count >= limit:
            from plugins.moderation import apply_warn_punishment

            action = await apply_warn_punishment(bot, chat_id, user_id, settings.get("warn_mode", "ban"))
            await db.reset_warns(chat_id, user_id)
            return f"warn+{action}"
        return f"warn {count}/{limit}"
    if kind == "mute":
        await safe(bot.restrict_chat_member, chat_id, user_id, permissions=MUTE_PERMISSIONS)
        return "mute"
    if kind == "tmute":
        await safe(bot.restrict_chat_member, chat_id, user_id, permissions=MUTE_PERMISSIONS,
                   until_date=timedelta(seconds=duration or 600))
        return f"tmute {human_time(duration or 600)}"
    if kind == "kick":
        await kick(bot, chat_id, user_id)
        return "kick"
    if kind == "ban":
        await safe(bot.ban_chat_member, chat_id, user_id)
        return "ban"
    if kind == "tban":
        await safe(bot.ban_chat_member, chat_id, user_id,
                   until_date=timedelta(seconds=duration or 3600))
        return f"tban {human_time(duration or 3600)}"
    return "delete"


# ------------------------------------------------------------------ locks
@router.message(Command("lock", "unlock"))
async def cmd_lock(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    args = [a.lower().strip(",") for a in (command.args or "").split() if a.strip(",")]
    if not args:
        await message.reply("/lock url sticker gif …  ·  /locktypes")
        return
    known = [a for a in args if a in LOCK_TYPES]
    unknown = [a for a in args if a not in LOCK_TYPES]
    if unknown:
        await message.reply(i18n.t(lang, "lock_unknown", items=", ".join(unknown)))
    if not known:
        return
    settings = await db.get_chat(message.chat.id)
    locks = set(json.loads(settings.get("locks") or "[]"))
    if command.command == "lock":
        locks |= set(known)
    else:
        locks -= set(known)
    await db.update_chat(message.chat.id, locks=json.dumps(sorted(locks)))
    labels = ", ".join(LOCK_LABELS_MY.get(k, k) if lang == "my" else k for k in known)
    key = "lock_done" if command.command == "lock" else "unlock_done"
    await message.reply(i18n.t(lang, key, items=labels))


@router.message(Command("locks"))
async def cmd_locks(message: Message, bot: Bot) -> None:
    lang = await lang_of(message)
    settings = await db.get_chat(message.chat.id)
    locks = json.loads(settings.get("locks") or "[]")
    if not locks:
        await message.reply(i18n.t(lang, "locks_none"))
        return
    items = "\n".join(
        f"• {LOCK_LABELS_MY.get(k, k) if lang == 'my' else k} (<code>{k}</code>)" for k in locks
    )
    await message.reply(i18n.t(lang, "locks_list", items=items))


@router.message(Command("locktypes"))
async def cmd_locktypes(message: Message) -> None:
    lang = await lang_of(message)
    items = ", ".join(f"<code>{k}</code>" for k in LOCK_TYPES)
    await message.reply(i18n.t(lang, "locktypes_list", items=items))


# ------------------------------------------------------------------ blocklist
@router.message(Command("addblocklist", "blocklist_add"))
async def cmd_addblock(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    word = (command.args or "").strip()
    if not word:
        await message.reply("/addblocklist <စကားလုံး>")
        return
    await db.add_block(message.chat.id, word.lower())
    await message.reply(i18n.t(lang, "block_added", word=html.escape(word)))


@router.message(Command("unblocklist", "rmblocklist", "unblock"))
async def cmd_unblock(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    word = (command.args or "").strip()
    if not word:
        await message.reply("/unblocklist <စကားလုံး>")
        return
    await db.del_block(message.chat.id, word.lower())
    await message.reply(i18n.t(lang, "block_removed", word=html.escape(word)))


@router.message(Command("unblocklistall"))
async def cmd_unblock_all(message: Message, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    await db.clear_blocks(message.chat.id)
    await message.reply(i18n.t(lang, "blocks_cleared"))


@router.message(Command("blocklist"))
async def cmd_blocklist(message: Message, bot: Bot) -> None:
    lang = await lang_of(message)
    words = await db.list_blocks(message.chat.id)
    if not words:
        await message.reply(i18n.t(lang, "blocklist_empty"))
        return
    items = "\n".join(f"• <code>{html.escape(w)}</code>" for w in words[:60])
    await message.reply(i18n.t(lang, "blocklist_list", n=len(words), items=items))


@router.message(Command("blocklistmode"))
async def cmd_blocklistmode(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    mode = (command.args or "").strip().lower()
    valid = ("delete", "warn", "mute", "kick", "ban")
    if mode.split()[0] not in valid and not mode.startswith(("tmute", "tban")):
        await message.reply("/blocklistmode delete|warn|mute|tmute 10m|kick|ban|tban 1d")
        return
    await db.update_chat(message.chat.id, blocklist_mode=mode)
    await message.reply(i18n.t(lang, "blocklist_mode_set", mode=mode))


# ------------------------------------------------------------------ antiflood
@router.message(Command("setflood"))
async def cmd_setflood(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    arg = (command.args or "").strip()
    if arg in ("off", "0", "no"):
        await db.update_chat(message.chat.id, flood=0)
        await message.reply(i18n.t(lang, "flood_off"))
        return
    if not arg.isdigit():
        await message.reply("/setflood 5   (0 = ပိတ်)")
        return
    await db.update_chat(message.chat.id, flood=int(arg))
    await message.reply(i18n.t(lang, "flood_set", n=int(arg)))


@router.message(Command("setfloodtimer"))
async def cmd_setfloodtimer(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    parts = (command.args or "").split()
    if len(parts) < 2 or not parts[0].isdigit():
        await message.reply("/setfloodtimer 5 10s")
        return
    seconds = parse_time(parts[1])
    if not seconds:
        await message.reply(i18n.t(lang, "err_bad_time"))
        return
    await db.update_chat(message.chat.id, flood_win=int(parts[0]), flood_win_seconds=seconds)
    await message.reply(i18n.t(lang, "flood_timer_set", n=int(parts[0]), window=seconds))


@router.message(Command("setfloodmode"))
async def cmd_setfloodmode(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    mode = (command.args or "").strip().lower()
    if not mode:
        await message.reply("/setfloodmode mute|tmute 10m|kick|ban|tban 1d")
        return
    await db.update_chat(message.chat.id, flood_mode=mode)
    await message.reply(i18n.t(lang, "flood_mode_set", mode=mode))


@router.message(Command("flood"))
async def cmd_flood(message: Message, bot: Bot) -> None:
    lang = await lang_of(message)
    settings = await db.get_chat(message.chat.id)
    window = (f"{settings.get('flood_win')} / {settings.get('flood_win_seconds')}s"
              if settings.get("flood_win") else "—")
    await message.reply(i18n.t(
        lang, "flood_info",
        limit=settings.get("flood", 0),
        window=window,
        mode=settings.get("flood_mode", "mute"),
        clear="on" if settings.get("clearflood") else "off",
    ))


@router.message(Command("clearflood"))
async def cmd_clearflood(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    arg = (command.args or "").strip().lower()
    on = arg in ("on", "yes", "true", "1")
    await db.update_chat(message.chat.id, clearflood=1 if on else 0)
    await message.reply(i18n.t(lang, "clearflood_on" if on else "clearflood_off"))


# ------------------------------------------------------------------ antiraid
@router.message(Command("antiraid"))
async def cmd_antiraid(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    arg = (command.args or "").strip().lower()
    on = arg in ("on", "yes", "true", "1")
    await db.update_chat(message.chat.id, antiraid=1 if on else 0)
    await message.reply(i18n.t(lang, "antiraid_on" if on else "antiraid_off"))


@router.message(Command("raidtime"))
async def cmd_raidtime(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    seconds = parse_time((command.args or "").strip())
    if not seconds:
        await message.reply(i18n.t(lang, "err_bad_time"))
        return
    await db.update_chat(message.chat.id, antiraid_time=seconds)
    await message.reply(i18n.t(lang, "antiraid_time_set", time=human_time(seconds)))


@router.message(Command("raidlimit"))
async def cmd_raidlimit(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    arg = (command.args or "").strip()
    if not arg.isdigit():
        await message.reply("/raidlimit 8")
        return
    await db.update_chat(message.chat.id, antiraid_limit=int(arg))
    await message.reply(f"✅ AntiRaid limit = {arg}")


async def antiraid_check(bot: Bot, message: Message, join_times: deque, settings: dict) -> bool:
    """Join အများကြီး တစ်ချိန်တည်း ဖြစ်ရင် group ကို ခေတ္တ lock ချတယ်။"""
    now = time.monotonic()
    join_times.append(now)
    window = 30
    while join_times and now - join_times[0] > window:
        join_times.popleft()
    limit = int(settings.get("antiraid_limit") or 8)
    if len(join_times) < limit:
        return False
    count = len(join_times)
    join_times.clear()
    seconds = int(settings.get("antiraid_time") or 3600)
    chat_id = message.chat.id
    await safe(bot.set_chat_permissions, chat_id,
               permissions=ChatPermissions(can_send_messages=False))
    lang = await lang_of(message)
    await message.answer(i18n.t(lang, "antiraid_triggered", n=count, time=human_time(seconds)))
    asyncio.create_task(_restore_permissions(bot, chat_id, seconds, lang))
    return True


async def _restore_permissions(bot: Bot, chat_id: int, seconds: int, lang: str) -> None:
    import asyncio

    await asyncio.sleep(seconds)
    await safe(bot.set_chat_permissions, chat_id, permissions=ChatPermissions(
        can_send_messages=True, can_send_audios=True, can_send_documents=True,
        can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
        can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
        can_add_web_page_previews=True, can_react_to_messages=True,
    ))
    await safe(bot.send_message, chat_id, "🔓 AntiRaid lock ပြန်ဖွင့်ပြီး။" if lang == "my"
               else "🔓 AntiRaid lock lifted.")
