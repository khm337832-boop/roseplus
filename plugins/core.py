"""core.py — /start, /help, /lang, /id, /info, /ping, /stats, /export, /import, command ပိတ်/ဖွင့်"""
from __future__ import annotations

import html
import json
import time
from io import BytesIO

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import db
import i18n
from common import chat_lang, lang_of, log_action
from config import BOT_NAME, BOT_USERNAME, DEFAULT_LANG, OWNER_ID
from helpers import is_admin, mention, name_of, require_admin

router = Router(name="core")


def lang_keyboard() -> InlineKeyboardMarkup:
    from plugins.menu import lang_keyboard as _lang_keyboard

    return _lang_keyboard()


# ------------------------------------------------------------------ start/help
@router.message(Command("start"))
async def cmd_start(message: Message, bot: Bot) -> None:
    lang = await chat_lang(message.chat.id)
    if message.from_user:
        await db.touch_user(message.from_user.id, lang)
        stored = await db.get_user_lang(message.from_user.id)
        if stored:
            lang = stored
    from plugins.menu import main_keyboard

    text = i18n.t(lang, "start", name=name_of(message.from_user), bot=BOT_NAME)
    markup = main_keyboard(lang, message.chat.type != "private", with_close=False)
    if message.chat.type != "private":
        await message.reply(text, reply_markup=markup)
        return
    await message.answer(text, reply_markup=markup)


@router.message(Command("help"))
async def cmd_help(message: Message, bot: Bot) -> None:
    """စာရှည်ကြီး တစ်ခါတည်း မပို့ဘဲ — button နဲ့ အပိုင်းလိုက် ကြည့်နိုင်အောင်။"""
    from plugins.menu import help_keyboard

    lang = await lang_of(message)
    text = i18n.t(lang, "help_choose")
    if message.chat.type == "private":
        await message.answer(text, reply_markup=help_keyboard(lang))
    else:
        await message.reply(text, reply_markup=help_keyboard(lang))


@router.callback_query(F.data.startswith("setlang:"))
async def cb_setlang(callback: CallbackQuery, bot: Bot) -> None:
    lang = callback.data.split(":", 1)[1]
    if lang not in i18n.available():
        await callback.answer()
        return
    if callback.from_user:
        await db.set_user_lang(callback.from_user.id, lang)
    if callback.message and callback.message.chat.type != "private":
        if not await is_admin(bot, callback.message.chat.id, callback.from_user.id):
            await callback.answer(i18n.t(lang, "err_admin_only"), show_alert=True)
            return
        await db.update_chat(callback.message.chat.id, lang=lang)
    key = "lang_set" if lang == "my" else "lang_set_en"
    await callback.answer(i18n.t(lang, key), show_alert=False)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass


@router.message(Command("lang", "setlang"))
async def cmd_lang(message: Message, command: CommandObject, bot: Bot) -> None:
    arg = (command.args or "").strip().lower()
    lang = await lang_of(message)
    if arg not in i18n.available():
        await message.reply(i18n.t(lang, "help_footer"), reply_markup=lang_keyboard())
        return
    if message.chat.type != "private":
        if not await require_admin(bot, message, lang, i18n.t):
            return
        await db.update_chat(message.chat.id, lang=arg)
    if message.from_user:
        await db.set_user_lang(message.from_user.id, arg)
    await message.reply(i18n.t(arg, "lang_set" if arg == "my" else "lang_set_en"))


# ------------------------------------------------------------------ info
@router.message(Command("id"))
async def cmd_id(message: Message) -> None:
    lang = await lang_of(message)
    target = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    await message.reply(i18n.t(
        lang, "id_text",
        chat_id=message.chat.id,
        user_id=target.id if target else message.from_user.id if message.from_user else 0,
    ))


@router.message(Command("info"))
async def cmd_info(message: Message, command: CommandObject, bot: Bot) -> None:
    from helpers import extract_target

    lang = await lang_of(message)
    user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    uid = user.id if user else 0
    if not message.reply_to_message and command.args:
        found, _name, _rest = await extract_target(message, bot, command.args)
        if found:
            uid = found
            try:
                user = await bot.get_chat(uid)
            except Exception:
                pass
    count, reasons = await db.get_warn(message.chat.id, uid)
    trusted = await db.is_approved(message.chat.id, uid)
    await message.reply(i18n.t(
        lang, "info_text",
        name=html.escape(getattr(user, "full_name", None) or str(uid)),
        uid=uid,
        username=f"@{user.username}" if getattr(user, "username", None) else "—",
        warns=count,
        trusted="✅" if trusted else "—",
    ))


@router.message(Command("ping"))
async def cmd_ping(message: Message) -> None:
    lang = await lang_of(message)
    started = time.perf_counter()
    sent = await message.reply("🏓")
    ms = (time.perf_counter() - started) * 1000
    await sent.edit_text(i18n.t(lang, "ping", ms=f"{ms:.0f}"))


@router.message(Command("stats"))
async def cmd_stats(message: Message, bot: Bot) -> None:
    lang = await lang_of(message)
    if message.chat.type != "private" and not await require_admin(bot, message, lang, i18n.t):
        return
    settings = await db.get_chat(message.chat.id)
    await message.reply(i18n.t(
        lang, "stats_text",
        messages=settings.get("msg_count", 0),
        warns=await db.count_warns(message.chat.id),
        blocks=len(await db.list_blocks(message.chat.id)),
        filters=len(await db.list_filters(message.chat.id)),
        notes=len(await db.list_notes(message.chat.id)),
    ))


# ------------------------------------------------------------------ export / import
EXPORT_FIELDS = [
    "lang", "welcome", "welcome_on", "goodbye", "goodbye_on", "cleanwelcome", "cleanservice",
    "rules", "rules_private", "flood", "flood_mode", "flood_win", "flood_win_seconds",
    "clearflood", "warn_limit", "warn_mode", "warn_expiry", "captcha", "captcha_mode",
    "captcha_kick", "captcha_kick_time", "captcha_rules", "captcha_text", "antiraid",
    "antiraid_time", "antiraid_limit", "locks", "disabled", "blocklist_mode",
]


@router.message(Command("export"))
async def cmd_export(message: Message, bot: Bot) -> None:
    lang = await lang_of(message)
    if message.chat.type != "private" and not await require_admin(bot, message, lang, i18n.t):
        return
    settings = await db.get_chat(message.chat.id)
    data = {
        "version": 1,
        "chat": {k: settings.get(k) for k in EXPORT_FIELDS},
        "notes": {n: await db.get_note(message.chat.id, n) for n in await db.list_notes(message.chat.id)},
        "filters": [
            {k: f[k] for k in ("trigger", "reply", "admin_only", "protect")}
            for f in await db.list_filters(message.chat.id)
        ],
        "blocklist": await db.list_blocks(message.chat.id),
    }
    buf = BytesIO(json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"))
    await message.reply_document(
        document=("goii_settings.json", buf),
        caption=i18n.t(lang, "export_done"),
    )


@router.message(Command("import"))
async def cmd_import(message: Message, bot: Bot) -> None:
    lang = await lang_of(message)
    if message.chat.type != "private" and not await require_admin(bot, message, lang, i18n.t):
        return
    document = message.document or (message.reply_to_message.document if message.reply_to_message else None)
    if document is None:
        await message.reply(i18n.t(lang, "import_err"))
        return
    try:
        buf = BytesIO()
        await bot.download(document, destination=buf)
        data = json.loads(buf.getvalue().decode("utf-8"))
        fields = {k: v for k, v in data.get("chat", {}).items() if k in EXPORT_FIELDS}
        if fields:
            await db.update_chat(message.chat.id, **fields)
        for name, content in (data.get("notes") or {}).items():
            if content:
                await db.save_note(message.chat.id, name, content)
        for f in data.get("filters") or []:
            if f.get("trigger") and f.get("reply"):
                await db.set_filter(message.chat.id, f["trigger"], f["reply"],
                                    int(f.get("admin_only", 0)), int(f.get("protect", 0)))
        for word in data.get("blocklist") or []:
            await db.add_block(message.chat.id, word)
    except Exception:
        await message.reply(i18n.t(lang, "import_err"))
        return
    await message.reply(i18n.t(lang, "import_done"))


# ------------------------------------------------------------------ disable / enable / log channel
@router.message(Command("disable"))
async def cmd_disable(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    cmd = (command.args or "").strip().split()[0].lstrip("/").lower() if command.args else ""
    if not cmd:
        await message.reply("/disable <command>")
        return
    settings = await db.get_chat(message.chat.id)
    disabled = set(json.loads(settings.get("disabled") or "[]"))
    disabled.add(cmd)
    await db.update_chat(message.chat.id, disabled=json.dumps(sorted(disabled)))
    await message.reply(i18n.t(lang, "disabled_added", cmd=cmd))


@router.message(Command("enable"))
async def cmd_enable(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    cmd = (command.args or "").strip().split()[0].lstrip("/").lower() if command.args else ""
    settings = await db.get_chat(message.chat.id)
    disabled = set(json.loads(settings.get("disabled") or "[]"))
    disabled.discard(cmd)
    await db.update_chat(message.chat.id, disabled=json.dumps(sorted(disabled)))
    await message.reply(i18n.t(lang, "disabled_removed", cmd=cmd))


@router.message(Command("disabled"))
async def cmd_disabled(message: Message, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    settings = await db.get_chat(message.chat.id)
    items = json.loads(settings.get("disabled") or "[]")
    if not items:
        await message.reply(i18n.t(lang, "disabled_empty"))
        return
    await message.reply(i18n.t(lang, "disabled_list",
                               items="\n".join(f"• <code>{c}</code>" for c in items)))


@router.message(Command("logchannel", "setlog"))
async def cmd_logchannel(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    arg = (command.args or "").strip()
    if arg.lower() in ("off", "no", "0"):
        await db.update_chat(message.chat.id, log_channel=0)
        await message.reply(i18n.t(lang, "log_channel_off"))
        return
    channel_id = 0
    if message.reply_to_message and message.reply_to_message.sender_chat:
        channel_id = message.reply_to_message.sender_chat.id
    elif arg:
        try:
            channel = await bot.get_chat(arg)
            channel_id = channel.id
        except Exception:
            channel_id = 0
    if not channel_id:
        await message.reply("/logchannel @mychannel  (သို့) channel post ကို reply ပြန်ပါ")
        return
    try:
        await bot.send_message(channel_id, "✅ Goii Auto Bot log channel connected.")
    except Exception:
        await message.reply("⚠️ အဲ့ channel ကို ကျွန်တော် message ပို့လို့ မရပါ — admin ပေးပါ။")
        return
    await db.update_chat(message.chat.id, log_channel=channel_id)
    await message.reply(i18n.t(lang, "log_channel_set"))


# ------------------------------------------------------------------ owner broadcast (optional)
@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, command: CommandObject, bot: Bot) -> None:
    if not OWNER_ID or not message.from_user or message.from_user.id != OWNER_ID:
        return
    if not command.args:
        return
    sent = failed = 0
    for chat in await db.all_chats():
        try:
            await bot.send_message(chat["chat_id"], command.args)
            sent += 1
        except Exception:
            failed += 1
    await message.reply(f"✅ sent={sent} failed={failed}")
