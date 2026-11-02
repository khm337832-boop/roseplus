"""gate.py — force-join (channel ကို join မလုပ်ရင် bot ကို မသုံးနိုင်အောင် တားဆီးတယ်)။

ဘယ်လို အလုပ်လုပ်လဲ
  • message တိုင်း မတိုင်မီ user က channel ထဲ ရှိမရှိ စစ်တယ် (cache ၆၀ စက္ကန့်)
  • မရှိရင် "join" + "စစ်ဆေးမယ်" button ပြတယ်၊ ကျန်တဲ့ command တွေ မအလုပ်လုပ်ဘူး
  • owner (OWNER_ID) က ကင်းလွတ်တယ်
  • channel ကို မစစ်နိုင်ရင် (bot admin မဟုတ် / username မှား) — bot မရပ်စေဖို့ ခွင့်ပြုလိုက်တယ်
"""
from __future__ import annotations

import logging
import time

from aiogram import Bot, F, Router
from aiogram.dispatcher.event.bases import CancelHandler
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

import config
import db
import i18n
from common import lang_of
from helpers import is_admin

log = logging.getLogger("goii.gate")
router = Router(name="gate")

_MEMBERSHIP_TTL = 60
_cache: dict[int, tuple[bool, float]] = {}
_verified = False      # channel ကို စစ်လို့ ရမရ (ရမှ force-join အလုပ်လုပ်)
_warned = False


def gate_keyboard(lang: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=i18n.t(lang, "gate_btn_join"), url=config.FORCE_SUB_URL)],
        [InlineKeyboardButton(text=i18n.t(lang, "gate_btn_check"), callback_data="gate:check")],
    ])


async def _channel_id(bot: Bot) -> int | None:
    """Channel id ကို ရှာတယ်။ တစ်ခါတည်း cache လုပ်တယ်။"""
    global _verified
    try:
        chat = await bot.get_chat(config.FORCE_SUB_CHANNEL)
    except Exception as exc:
        log.warning("force-sub: channel %s ကို မတွေ့ပါ (%s)", config.FORCE_SUB_CHANNEL, exc)
        _verified = False
        return None
    if chat.type not in ("channel", "supergroup", "group"):
        log.warning("force-sub: %s က channel မဟုတ်ပါ (type=%s) — force-join ပိတ်ထားလိုက်တယ်",
                    config.FORCE_SUB_CHANNEL, chat.type)
        _verified = False
        return None
    _verified = True
    return chat.id


async def status(bot: Bot, user_id: int) -> dict:
    """diagnostic အတွက် force-join အခြေအနေ။"""
    out: dict = {"enabled": config.force_sub_enabled(), "channel": config.FORCE_SUB_CHANNEL,
                 "resolvable": False, "member": None}
    if not out["enabled"]:
        return out
    chat_id = await _channel_id(bot)
    if chat_id is not None:
        out["resolvable"] = True
        try:
            m = await bot.get_chat_member(chat_id, user_id)
            out["member"] = m.status in ("member", "administrator", "creator")
        except Exception:
            out["member"] = None
    return out


async def is_member(bot: Bot, user_id: int) -> bool:
    if not config.force_sub_enabled():
        return True
    now = time.monotonic()
    hit = _cache.get(user_id)
    if hit and hit[1] > now:
        return hit[0]
    chat_id = await _channel_id(bot)
    if chat_id is None:
        return True          # မစစ်နိုင်ရင် ခွင့်ပြု (bot မရပ်စေဖို့)
    try:
        member = await bot.get_chat_member(chat_id, user_id)
        ok = member.status in ("member", "administrator", "creator")
    except Exception as exc:
        global _warned
        if not _warned:
            _warned = True
            log.warning("force-sub: membership စစ်လို့ မရ (%s) — channel မှာ bot ကို admin ပေးပါ။ "
                        "ဒီအချိန်မှာ force-join ကို ခေတ္တ ပိတ်ထားတယ်။", exc)
        return True
    _cache[user_id] = (ok, now + _MEMBERSHIP_TTL)
    return ok


def forget(user_id: int) -> None:
    _cache.pop(user_id, None)


async def send_gate(message: Message, lang: str, group: bool = False) -> None:
    text = i18n.t(lang, "gate_text_admin" if group else "gate_text")
    try:
        await message.answer(text, reply_markup=gate_keyboard(lang), disable_web_page_preview=True)
    except Exception:
        pass


class ForceJoinMiddleware:
    """message တိုင်းရဲ့ အရှေ့မှာ channel join ကို စစ်တယ်။"""

    async def __call__(self, handler, event, data):
        if not config.force_sub_enabled():
            return await handler(event, data)
        bot: Bot | None = data.get("bot")
        user = getattr(event, "from_user", None)
        if bot is None or user is None or user.is_bot:
            return await handler(event, data)
        if config.OWNER_ID and user.id == config.OWNER_ID:
            return await handler(event, data)
        in_group = (
            (isinstance(event, Message) and event.chat.type in ("group", "supergroup"))
            or (isinstance(event, CallbackQuery) and event.message is not None
                and event.message.chat.type in ("group", "supergroup"))
        )
        if in_group:
            # ---- group ထဲမှာ admin တွေပဲ စစ်တယ် (member တွေကို မနှောင့်ယှက်) ----
            from_ = event.from_user
            chat_id = event.chat.id if isinstance(event, Message) else event.message.chat.id
            if not await is_admin(bot, chat_id, from_.id):
                return await handler(event, data)
            if isinstance(event, Message):
                text = (event.text or "").strip()
                from plugins.menu import is_menu_text

                # command (သို့) keyboard button မဟုတ်ရင် ရိုးရိုးစကားပြောတာမို့ မစစ်
                if not text.startswith("/") and not is_menu_text(text):
                    return await handler(event, data)
        lang = await db.get_user_lang(user.id) or config.DEFAULT_LANG
        if await is_member(bot, user.id):
            return await handler(event, data)
        if isinstance(event, CallbackQuery):
            if event.data == "gate:check":
                return await handler(event, data)
            await event.answer(i18n.t(lang, "gate_not_yet"), show_alert=True)
            raise CancelHandler()
        if isinstance(event, Message):
            await send_gate(event, lang, in_group)
        raise CancelHandler()


# ----------------------------------------------------------------- callbacks
@router.callback_query(F.data == "gate:check")
async def cb_gate_check(callback: CallbackQuery, bot: Bot) -> None:
    user = callback.from_user
    if user is None:
        await callback.answer()
        return
    forget(user.id)
    lang = await db.get_user_lang(user.id) or config.DEFAULT_LANG
    if await is_member(bot, user.id):
        await callback.answer(i18n.t(lang, "gate_ok"), show_alert=True)
        if callback.message:
            try:
                await callback.message.edit_text(i18n.t(lang, "gate_ok"), reply_markup=None)
            except Exception:
                pass
    else:
        await callback.answer(i18n.t(lang, "gate_not_yet"), show_alert=True)
