"""settings.py — /settings button panel (command ကျက်စရာမလိုဘဲ နှိပ်ရုံ setting ချိန်နိုင်)"""
from __future__ import annotations

import json

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import db
import i18n
from common import chat_lang
from helpers import is_admin

router = Router(name="settings")

QUICK_LOCKS = ["url", "forward", "sticker", "gif", "media", "mentions"]


def _state(lang: str, value) -> str:
    return i18n.t(lang, "on" if value else "off")


def _panel_keyboard(lang: str, settings: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"{i18n.t(lang, 'btn_welcome')} {_state(lang, settings.get('welcome_on'))}",
                                 callback_data="st:toggle:welcome_on"),
            InlineKeyboardButton(text=f"{i18n.t(lang, 'btn_captcha')} {_state(lang, settings.get('captcha'))}",
                                 callback_data="st:toggle:captcha"),
        ],
        [
            InlineKeyboardButton(text=f"{i18n.t(lang, 'btn_flood')} {_state(lang, settings.get('flood'))}",
                                 callback_data="st:toggle:flood"),
            InlineKeyboardButton(text=f"{i18n.t(lang, 'btn_antiraid')} {_state(lang, settings.get('antiraid'))}",
                                 callback_data="st:toggle:antiraid"),
        ],
        [
            InlineKeyboardButton(text=i18n.t(lang, "btn_locks"), callback_data="st:locks"),
            InlineKeyboardButton(text=f"{i18n.t(lang, 'btn_lang')} ({settings.get('lang', 'my')})",
                                 callback_data="st:lang"),
        ],
        [InlineKeyboardButton(text=i18n.t(lang, "btn_settings_done"), callback_data="st:close")],
    ])


def _locks_keyboard(lang: str, locks: set[str]) -> InlineKeyboardMarkup:
    rows, row = [], []
    for lock in QUICK_LOCKS:
        mark = "✅" if lock in locks else "▫️"
        row.append(InlineKeyboardButton(text=f"{mark} {lock}", callback_data=f"st:lock:{lock}"))
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text=i18n.t(lang, "btn_settings_refresh"), callback_data="st:main")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def _render(chat_id: int) -> tuple[str, InlineKeyboardMarkup]:
    settings = await db.get_chat(chat_id)
    lang = settings.get("lang") or "my"
    locks = json.loads(settings.get("locks") or "[]")
    text = i18n.t(
        lang, "settings_title",
        chat=settings.get("title") or str(chat_id),
        language=i18n.t(lang, "lang_name"),
        welcome=_state(lang, settings.get("welcome_on")),
        captcha=_state(lang, settings.get("captcha")),
        flood=_state(lang, settings.get("flood")),
        locks=str(len(locks)),
        antiraid=_state(lang, settings.get("antiraid")),
    )
    return text, _panel_keyboard(lang, settings)


@router.message(Command("settings", "panel"))
async def cmd_settings(message: Message, bot: Bot) -> None:
    lang = await chat_lang(message.chat.id)
    if message.chat.type != "private" and not await is_admin(bot, message.chat.id, message.from_user.id):
        await message.reply(i18n.t(lang, "err_admin_only"))
        return
    if message.chat.type != "private":
        await db.update_chat(message.chat.id, title=message.chat.title or "")
    text, markup = await _render(message.chat.id)
    await message.reply(text, reply_markup=markup)


@router.callback_query(F.data.startswith("st:"))
async def cb_settings(callback: CallbackQuery, bot: Bot) -> None:
    parts = callback.data.split(":")
    action = parts[1] if len(parts) > 1 else "main"
    chat_id = callback.message.chat.id
    if not await is_admin(bot, chat_id, callback.from_user.id):
        await callback.answer(i18n.t(await chat_lang(chat_id), "err_admin_only"), show_alert=True)
        return

    settings = await db.get_chat(chat_id)
    lang = settings.get("lang") or "my"

    if action == "close":
        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.answer()
        return

    if action == "toggle" and len(parts) > 2:
        field = parts[2]
        if field == "flood":
            new_value = 0 if settings.get("flood") else 5
        else:
            new_value = 0 if settings.get(field) else 1
        await db.update_chat(chat_id, **{field: new_value})
        if field == "captcha" and new_value:
            await db.update_chat(chat_id, welcome_on=1)

    if action == "lock" and len(parts) > 2:
        lock = parts[2]
        locks = set(json.loads(settings.get("locks") or "[]"))
        locks ^= {lock}
        await db.update_chat(chat_id, locks=json.dumps(sorted(locks)))

    if action == "lang":
        new_lang = "en" if lang == "my" else "my"
        await db.update_chat(chat_id, lang=new_lang)
        if callback.from_user:
            await db.set_user_lang(callback.from_user.id, new_lang)
        lang = new_lang

    settings = await db.get_chat(chat_id)
    if action == "locks":
        locks = set(json.loads(settings.get("locks") or "[]"))
        await callback.message.edit_text(
            i18n.t(lang, "locks_list", items=", ".join(sorted(locks)) or i18n.t(lang, "locks_none")),
            reply_markup=_locks_keyboard(lang, locks))
    else:
        text, markup = await _render(chat_id)
        await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()
