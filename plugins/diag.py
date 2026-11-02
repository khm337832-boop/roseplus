"""diag.py — /diag : command တွေ ဘာလို့ အလုပ်မလုပ်လဲ ကိုယ်တိုင် စစ်ဆေးနိုင်တဲ့ ကိရိယာ။"""
from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command
from aiogram.types import Message

import config
import db
import i18n
from common import lang_of
from plugins import gate

router = Router(name="diag")


@router.message(Command("diag", "check", "why"))
async def cmd_diag(message: Message, bot: Bot) -> None:
    lang = await lang_of(message)
    yes, no, unk = (i18n.t(lang, "diag_yes"), i18n.t(lang, "diag_no"), i18n.t(lang, "diag_unknown"))

    def row(label: str, value: str) -> str:
        return i18n.t(lang, "diag_line", label=label, value=value)

    lines = [i18n.t(lang, "diag_title"), ""]
    lines.append(row("Chat", f"{message.chat.title or message.chat.type} · <code>{message.chat.id}</code>"))

    # ---- သင် admin လား ----
    me_admin = unk
    if message.from_user:
        if config.OWNER_ID and message.from_user.id == config.OWNER_ID:
            me_admin = yes
        elif message.chat.type == "private":
            me_admin = "👤 private"
        else:
            try:
                m = await bot.get_chat_member(message.chat.id, message.from_user.id)
                me_admin = yes if m.status in ("administrator", "creator") else no
            except Exception:
                me_admin = unk
    lines.append(row("သင် admin", me_admin))

    # ---- bot က admin လား ----
    bot_admin = unk
    can_restrict = unk
    can_delete = unk
    try:
        bm = await bot.get_chat_member(message.chat.id, bot.id)
        bot_admin = yes if bm.status in ("administrator", "creator") else no
        can_restrict = yes if getattr(bm, "can_restrict_members", False) else no
        can_delete = yes if getattr(bm, "can_delete_messages", False) else no
    except Exception:
        pass
    lines.append(row("Bot admin", bot_admin))
    lines.append(row("Bot — mute/ban right", can_restrict))
    lines.append(row("Bot — delete right", can_delete))

    # ---- force-join ----
    st = await gate.status(bot, message.from_user.id if message.from_user else 0)
    lines.append(row("Force-join", ("🟢 on · " + st["channel"]) if st["enabled"] else "🔴 off"))
    if st["enabled"]:
        lines.append(row("Channel စစ်လို့ရ", yes if st["resolvable"] else no))
        if st["member"] is True:
            lines.append(row("သင် join ပြီးလား", yes))
        elif st["member"] is False:
            lines.append(row("သင် join ပြီးလား", no))
        else:
            lines.append(row("သင် join ပြီးလား", unk))

    lines.append(row("Database", db.backend_name()))
    lines.append(row("Owner id", str(config.OWNER_ID or "—")))
    lines.append("")
    lines.append(i18n.t(lang, "diag_help"))

    text = "\n".join(lines)
    if message.chat.type == "private":
        await message.answer(text, reply_markup=_keyboard(lang, st))
    else:
        await message.reply(text, reply_markup=_keyboard(lang, st))


def _keyboard(lang: str, st: dict):
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    rows = []
    if st.get("enabled") and st.get("member") is not True:
        rows.append([InlineKeyboardButton(text=i18n.t(lang, "gate_btn_join"), url=config.FORCE_SUB_URL),
                     InlineKeyboardButton(text=i18n.t(lang, "gate_btn_check"), callback_data="gate:check")])
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None
