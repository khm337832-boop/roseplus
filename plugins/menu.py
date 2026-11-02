"""menu.py — button နှိပ်ရုံနဲ့ သုံးနိုင်တဲ့ အဓိက menu (command ကျက်စရာ မလို)။

/menu  ·  /quick  ·  group ထဲ ထည့်ခံရတဲ့အခါ အလိုအလျောက် ကြိုဆိုစာ
"""
from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    ChatMemberUpdated,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import db
import i18n
from common import chat_lang
from config import BOT_NAME
from helpers import is_admin

router = Router(name="menu")

HELP_SECTIONS = ("mod", "spam", "greet", "other")


# ----------------------------------------------------------------- helpers
def _btn(text: str, data: str) -> InlineKeyboardButton:
    return InlineKeyboardButton(text=text, callback_data=data)


def _onoff(settings: dict, field: str, on_value=1) -> str:
    return "🟢" if settings.get(field) else "🔴"


def lang_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        _btn("🇲🇲 မြန်မာ", "setlang:my"),
        _btn("🇬🇧 English", "setlang:en"),
    ], [_btn(i18n.t("my", "menu_btn_back"), "mn:home")]])


def main_keyboard(lang: str, in_group: bool, with_close: bool = True) -> InlineKeyboardMarkup:
    rows = [
        [_btn(i18n.t(lang, "menu_btn_quick"), "mn:quick"),
         _btn(i18n.t(lang, "menu_btn_help"), "mn:help")],
    ]
    if in_group:
        rows.append([_btn(i18n.t(lang, "menu_btn_settings"), "st:main"),
                     _btn(i18n.t(lang, "menu_btn_lang"), "mn:lang")])
        rows.append([_btn(i18n.t(lang, "menu_btn_rules"), "mn:rules"),
                     _btn(i18n.t(lang, "menu_btn_id"), "mn:id")])
    else:
        rows.append([_btn(i18n.t(lang, "menu_btn_lang"), "mn:lang"),
                     _btn(i18n.t(lang, "menu_btn_id"), "mn:id")])
    if with_close:
        rows.append([_btn(i18n.t(lang, "menu_btn_close"), "mn:close")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def help_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn(i18n.t(lang, "help_btn_mod"), "mn:help:mod"),
         _btn(i18n.t(lang, "help_btn_spam"), "mn:help:spam")],
        [_btn(i18n.t(lang, "help_btn_greet"), "mn:help:greet"),
         _btn(i18n.t(lang, "help_btn_other"), "mn:help:other")],
        [_btn(i18n.t(lang, "help_btn_all"), "mn:help:all")],
        [_btn(i18n.t(lang, "menu_btn_back"), "mn:home")],
    ])


def quick_keyboard(lang: str, settings: dict) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [_btn(f"{_onoff(settings, 'welcome_on')} {i18n.t(lang, 'quick_btn_welcome')}",
              "mn:toggle:welcome_on"),
         _btn(f"{_onoff(settings, 'captcha')} {i18n.t(lang, 'quick_btn_captcha')}",
              "mn:toggle:captcha")],
        [_btn(f"{_onoff(settings, 'flood')} {i18n.t(lang, 'quick_btn_flood')}",
              "mn:toggle:flood"),
         _btn(i18n.t(lang, "menu_btn_settings"), "st:main")],
        [_btn(i18n.t(lang, "menu_btn_back"), "mn:home")],
    ])


def menu_text(lang: str) -> str:
    return i18n.t(lang, "menu_title", bot=BOT_NAME)


def quick_text(lang: str) -> str:
    return i18n.t(lang, "quick_title", bot=BOT_NAME)


def help_text(lang: str, section: str) -> str:
    key = {
        "mod": "help_mod",
        "spam": "help_spam" if i18n.t(lang, "help_spam") != "help_spam" else "help_antispam",
        "greet": "help_greetings",
        "other": "help_other",
    }.get(section, "help_mod")
    head = i18n.t(lang, "help_title", bot=BOT_NAME)
    if section == "all":
        return "\n\n".join([head, i18n.t(lang, "help_mod"), i18n.t(lang, "help_antispam"),
                            i18n.t(lang, "help_greetings"), i18n.t(lang, "help_other"),
                            i18n.t(lang, "help_footer")])
    return "\n\n".join([head, i18n.t(lang, key), i18n.t(lang, "help_footer")])


# ----------------------------------------------------------------- commands
@router.message(Command("menu", "buttons"))
async def cmd_menu(message: Message) -> None:
    lang = await chat_lang(message.chat.id)
    markup = main_keyboard(lang, message.chat.type != "private")
    if message.chat.type == "private":
        await message.answer(menu_text(lang), reply_markup=markup)
    else:
        await message.reply(menu_text(lang), reply_markup=markup)


@router.message(Command("quick", "start_here", "easy"))
async def cmd_quick(message: Message) -> None:
    lang = await chat_lang(message.chat.id)
    settings = await db.get_chat(message.chat.id)
    if message.chat.type == "private":
        await message.answer(quick_text(lang), reply_markup=quick_keyboard(lang, settings))
    else:
        await message.reply(quick_text(lang), reply_markup=quick_keyboard(lang, settings))


# ----------------------------------------------------------------- bot added to group
@router.my_chat_member()
async def on_bot_member_update(event: ChatMemberUpdated, bot: Bot) -> None:
    if event.chat.type not in ("group", "supergroup"):
        return
    if event.new_chat_member.user.id != bot.id:
        return
    was = event.old_chat_member.status
    now = event.new_chat_member.status
    if was in ("left", "kicked") and now in ("member", "administrator"):
        lang = await chat_lang(event.chat.id)
        await db.update_chat(event.chat.id, title=event.chat.title or "")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [_btn(i18n.t(lang, "added_group_btn"), "mn:quick")],
            [_btn(i18n.t(lang, "menu_btn_settings"), "st:main")],
        ])
        try:
            await bot.send_message(
                event.chat.id,
                i18n.t(lang, "added_group", bot=BOT_NAME, chat=event.chat.title or ""),
                reply_markup=keyboard,
            )
        except Exception:
            pass
    elif was in ("member", "administrator") and now == "administrator":
        # admin ဖြစ်သွားရင် အရေးကြီးဆုံး setting ကို တစ်ချက်ပဲ သတိပေး
        lang = await chat_lang(event.chat.id)
        try:
            await bot.send_message(event.chat.id, i18n.t(lang, "now_admin", bot=BOT_NAME),
                                   reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                                       [_btn(i18n.t(lang, "added_group_btn"), "mn:quick")]]))
        except Exception:
            pass


# ----------------------------------------------------------------- callbacks
@router.callback_query(F.data.startswith("mn:"))
async def cb_menu(callback: CallbackQuery, bot: Bot) -> None:
    parts = (callback.data or "").split(":")
    action = parts[1] if len(parts) > 1 else "home"
    message = callback.message
    if message is None:
        await callback.answer()
        return
    chat_id = message.chat.id
    in_group = message.chat.type != "private"
    lang = await chat_lang(chat_id)

    if action == "close":
        try:
            await message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        await callback.answer()
        return

    if action == "home":
        await _safe_edit(message, menu_text(lang), main_keyboard(lang, in_group))
        await callback.answer()
        return

    if action == "help":
        section = parts[2] if len(parts) > 2 else ""
        if section:
            await _safe_edit(message, help_text(lang, section), help_keyboard(lang))
        else:
            await _safe_edit(message, i18n.t(lang, "help_choose"), help_keyboard(lang))
        await callback.answer()
        return

    if action == "quick":
        settings = await db.get_chat(chat_id)
        await _safe_edit(message, quick_text(lang), quick_keyboard(lang, settings))
        await callback.answer()
        return

    if action == "lang":
        await _safe_edit(message, i18n.t(lang, "menu_lang_pick"), lang_keyboard())
        await callback.answer()
        return

    if action == "rules":
        settings = await db.get_chat(chat_id)
        text = settings.get("rules") or i18n.t(lang, "rules_empty")
        await callback.answer(text[:190], show_alert=True)
        return

    if action == "id":
        uid = callback.from_user.id if callback.from_user else 0
        await callback.answer(
            i18n.t(lang, "id_text", chat_id=chat_id, user_id=uid).replace("<code>", "").replace("</code>", ""),
            show_alert=True)
        return

    if action == "toggle" and len(parts) > 2:
        field = parts[2]
        if in_group and not await is_admin(bot, chat_id, callback.from_user.id):
            await callback.answer(i18n.t(lang, "err_admin_only"), show_alert=True)
            return
        if not in_group:
            await callback.answer(i18n.t(lang, "err_group_only"), show_alert=True)
            return
        settings = await db.get_chat(chat_id)
        if field == "flood":
            new_value = 0 if settings.get("flood") else 5
        else:
            new_value = 0 if settings.get(field) else 1
        await db.update_chat(chat_id, **{field: new_value})
        if field == "captcha" and new_value:
            # captcha က welcome message နဲ့ တွဲအလုပ်လုပ်တယ်
            await db.update_chat(chat_id, welcome_on=1)
        label = {
            "welcome_on": i18n.t(lang, "quick_btn_welcome"),
            "captcha": i18n.t(lang, "quick_btn_captcha"),
            "flood": i18n.t(lang, "quick_btn_flood"),
        }.get(field, field)
        await callback.answer(
            i18n.t(lang, "toggle_on" if new_value else "toggle_off", name=label))
        settings = await db.get_chat(chat_id)
        await _safe_edit(message, quick_text(lang), quick_keyboard(lang, settings))
        return

    await callback.answer()


async def _safe_edit(message: Message, text: str, markup: InlineKeyboardMarkup) -> None:
    try:
        await message.edit_text(text, reply_markup=markup, disable_web_page_preview=True)
    except Exception:
        try:
            await message.answer(text, reply_markup=markup, disable_web_page_preview=True)
        except Exception:
            pass
