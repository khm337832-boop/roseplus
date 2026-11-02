"""captcha.py — CAPTCHA (button / math), kick timeout, rules, background expiry job"""
from __future__ import annotations

import asyncio
import html
import random
import time

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
from common import lang_of
from helpers import (
    MUTE_PERMISSIONS,
    UNMUTE_PERMISSIONS,
    human_time,
    kick,
    mention,
    name_of,
    parse_time,
    require_admin,
    safe,
)

router = Router(name="captcha")

CAPTCHA_TIMEOUT = 300  # 5 မိနစ်


def _question() -> tuple[str, str]:
    a = random.randint(2, 12)
    b = random.randint(2, 9)
    op = random.choice(["+", "-", "×"])
    if op == "+":
        return f"{a} + {b}", str(a + b)
    if op == "-":
        a, b = max(a, b), min(a, b)
        return f"{a} - {b}", str(a - b)
    return f"{a} × {b}", str(a * b)


def _math_keyboard(chat_id: int, user_id: int, answer: str) -> InlineKeyboardMarkup:
    correct = int(answer)
    options = {correct}
    while len(options) < 4:
        delta = random.choice([-3, -2, -1, 1, 2, 3])
        if correct + delta > 0:
            options.add(correct + delta)
    options = list(options)
    random.shuffle(options)
    buttons = [
        InlineKeyboardButton(text=str(o), callback_data=f"capm:{chat_id}:{user_id}:{o}")
        for o in options
    ]
    return InlineKeyboardMarkup(inline_keyboard=[buttons[:2], buttons[2:]])


async def send_captcha(bot: Bot, message: Message, user, settings: dict, welcome_markup=None) -> None:
    """Member အသစ်ကို mute လုပ်ပြီး CAPTCHA ပို့တယ်။"""
    chat_id = message.chat.id
    lang = settings.get("lang") or "my"
    text_button = settings.get("captcha_text") or i18n.t(lang, "captcha_button")
    mode = settings.get("captcha_mode") or "button"
    kick_after = int(settings.get("captcha_kick_time") or CAPTCHA_TIMEOUT)

    await safe(bot.restrict_chat_member, chat_id, user.id, permissions=MUTE_PERMISSIONS)

    if mode == "math":
        question, answer = _question()
        await db.add_captcha(chat_id, user.id, int(time.time()) + kick_after, answer)
        sent = await message.reply(
            i18n.t(lang, "captcha_question", user=mention(user), question=question),
            reply_markup=_math_keyboard(chat_id, user.id, answer),
        )
    else:
        await db.add_captcha(chat_id, user.id, int(time.time()) + kick_after, "")
        markup = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text=text_button, callback_data=f"cap:{chat_id}:{user.id}")
        ]])
        try:
            sent = await message.reply(
                i18n.t(lang, "captcha_button_hint", user=mention(user)),
                reply_markup=markup,
            )
        except Exception:
            sent = await message.answer("…", reply_markup=markup)

    if settings.get("captcha_rules"):
        rules = settings.get("rules") or ""
        if rules:
            await safe(message.answer, i18n.t(lang, "captcha_rules_note") + "\n\n" + rules,
                       disable_web_page_preview=True)


# ------------------------------------------------------------------ callbacks
@router.callback_query(F.data.startswith("cap:"))
async def cb_captcha_button(callback: CallbackQuery, bot: Bot) -> None:
    _, chat_id_s, user_id_s = callback.data.split(":")
    chat_id, user_id = int(chat_id_s), int(user_id_s)
    settings = await db.get_chat(chat_id)
    lang = settings.get("lang") or "my"
    if callback.from_user.id != user_id:
        await callback.answer(i18n.t(lang, "captcha_not_yours"), show_alert=True)
        return
    await safe(bot.restrict_chat_member, chat_id, user_id, permissions=UNMUTE_PERMISSIONS)
    await db.del_captcha(chat_id, user_id)
    await callback.answer(i18n.t(lang, "captcha_solved", user=name_of(callback.from_user)),
                          show_alert=True)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass


@router.callback_query(F.data.startswith("capm:"))
async def cb_captcha_math(callback: CallbackQuery, bot: Bot) -> None:
    _, chat_id_s, user_id_s, answer = callback.data.split(":")
    chat_id, user_id = int(chat_id_s), int(user_id_s)
    settings = await db.get_chat(chat_id)
    lang = settings.get("lang") or "my"
    if callback.from_user.id != user_id:
        await callback.answer(i18n.t(lang, "captcha_not_yours"), show_alert=True)
        return
    pending = [c for c in await db.all_captchas() if c["chat_id"] == chat_id and c["user_id"] == user_id]
    if not pending:
        await callback.answer(i18n.t(lang, "captcha_solved", user=name_of(callback.from_user)),
                              show_alert=True)
        return
    if answer != (pending[0].get("answer") or ""):
        await callback.answer(i18n.t(lang, "captcha_wrong"), show_alert=True)
        return
    await safe(bot.restrict_chat_member, chat_id, user_id, permissions=UNMUTE_PERMISSIONS)
    await db.del_captcha(chat_id, user_id)
    await callback.answer(i18n.t(lang, "captcha_solved", user=name_of(callback.from_user)),
                          show_alert=True)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass


# ------------------------------------------------------------------ background job
async def expiry_worker(bot: Bot) -> None:
    """CAPTCHA မဖြေတဲ့ လူတွေကို အချိန်ပြည့်ရင် kick လုပ်တယ်။"""
    while True:
        try:
            for row in await db.expired_captchas():
                settings = await db.get_chat(row["chat_id"])
                lang = settings.get("lang") or "my"
                if settings.get("captcha_kick"):
                    await kick(bot, row["chat_id"], row["user_id"])
                    await safe(bot.send_message, row["chat_id"], i18n.t(
                        lang, "captcha_expired", user=f'<a href="tg://user?id={row["user_id"]}">user</a>'))
                await db.del_captcha(row["chat_id"], row["user_id"])
        except Exception:
            pass
        await asyncio.sleep(20)


# ------------------------------------------------------------------ commands
@router.message(Command("captcha"))
async def cmd_captcha(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    arg = (command.args or "").strip().lower()
    if arg not in ("on", "off"):
        settings = await db.get_chat(message.chat.id)
        state = i18n.t(lang, "on") if settings.get("captcha") else i18n.t(lang, "off")
        await message.reply(f"/captcha on|off  —  {state}")
        return
    on = arg == "on"
    await db.update_chat(message.chat.id, captcha=1 if on else 0)
    if on:
        await db.update_chat(message.chat.id, welcome_on=1)
    await message.reply(i18n.t(lang, "captcha_on" if on else "captcha_off"))


@router.message(Command("captchamode"))
async def cmd_captchamode(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    mode = (command.args or "").strip().lower()
    if mode not in ("button", "math"):
        await message.reply("/captchamode button|math")
        return
    await db.update_chat(message.chat.id, captcha_mode=mode)
    await message.reply(i18n.t(lang, "captcha_mode_set", mode=mode))


@router.message(Command("captchakick"))
async def cmd_captchakick(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    arg = (command.args or "").strip().lower()
    on = arg == "on"
    await db.update_chat(message.chat.id, captcha_kick=1 if on else 0)
    settings = await db.get_chat(message.chat.id)
    if on:
        await message.reply(i18n.t(lang, "captcha_kick_on",
                                   time=human_time(int(settings.get("captcha_kick_time") or 300))))
    else:
        await message.reply(i18n.t(lang, "captcha_kick_off"))


@router.message(Command("captchakicktime"))
async def cmd_captchakicktime(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    seconds = parse_time((command.args or "").strip())
    if not seconds or seconds < 60:
        await message.reply(i18n.t(lang, "err_bad_time"))
        return
    await db.update_chat(message.chat.id, captcha_kick_time=seconds)
    await message.reply(i18n.t(lang, "captcha_kick_on", time=human_time(seconds)))


@router.message(Command("captcharules"))
async def cmd_captcharules(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    on = (command.args or "").strip().lower() == "on"
    await db.update_chat(message.chat.id, captcha_rules=1 if on else 0)
    await message.reply(i18n.t(lang, "captcha_rules_on" if on else "captcha_rules_off"))


@router.message(Command("setcaptchatext"))
async def cmd_setcaptchatext(message: Message, command: CommandObject, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    text = (command.args or "").strip()
    if not text:
        await message.reply("/setcaptchatext စာသား")
        return
    await db.update_chat(message.chat.id, captcha_text=text[:60])
    await message.reply(i18n.t(lang, "captcha_text_set", text=html.escape(text[:60])))


@router.message(Command("resetcaptchatext"))
async def cmd_resetcaptchatext(message: Message, bot: Bot) -> None:
    lang = await lang_of(message)
    if not await require_admin(bot, message, lang, i18n.t):
        return
    await db.update_chat(message.chat.id, captcha_text="")
    await message.reply(i18n.t(lang, "captcha_text_set", text=i18n.t(lang, "captcha_button")))
