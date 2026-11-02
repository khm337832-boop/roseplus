"""tools/dryrun.py — Telegram ကို မချိတ်ဘဲ handler တွေ အလုပ်လုပ်မလုပ် စမ်းသပ်တယ်။
Telegram API ကို mock လုပ်ပြီး update တွေ တိုက်ရိုက် ထည့်စမ်းတာ။
run: python tools/dryrun.py
"""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from contextlib import ExitStack
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ["BOT_TOKEN"] = "123456:TESTTOKEN"

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import (  # noqa: E402
    Chat,
    ChatMemberAdministrator,
    ChatMemberMember,
    Message,
    Update,
    User,
)

import db  # noqa: E402
import i18n  # noqa: E402
from bot import DisabledCommandMiddleware, register_chat_middleware  # noqa: E402
from plugins import (  # noqa: E402
    antispam, captcha, content, core, federation, greetings, moderation, settings, watcher,
)

CAPTURED: list[dict] = []
FAILS: list[str] = []

GROUP = Chat(id=-1001234567890, type="supergroup", title="Test Group")
ADMIN = User(id=111, is_bot=False, first_name="Admin")
MEMBER = User(id=222, is_bot=False, first_name="Member")
BOT_USER = User(id=999, is_bot=True, first_name="RosePlus", username="RosePlusBot")


def check(name: str, cond: bool, extra: str = "") -> None:
    if cond:
        print(f"  ✅ {name}")
    else:
        FAILS.append(name)
        print(f"  ❌ {name} {extra}")


def last_text() -> str:
    return CAPTURED[-1]["text"] if CAPTURED else ""


# ------------------------------------------------------------------ mocks
async def fake_reply(self, text=None, **kwargs):
    CAPTURED.append({"kind": "reply", "text": text or "", "kwargs": kwargs, "self": self})
    return Message(message_id=9990 + len(CAPTURED), date=datetime.now(), chat=self.chat,
                   text=text or "")


async def fake_answer(self, text=None, **kwargs):
    CAPTURED.append({"kind": "answer", "text": text or "", "kwargs": kwargs, "self": self})
    return Message(message_id=9990 + len(CAPTURED), date=datetime.now(), chat=self.chat,
                   text=text or "")


async def fake_delete(self, *args, **kwargs):
    CAPTURED.append({"kind": "delete", "text": "<delete>", "kwargs": kwargs, "self": self})
    return True


async def fake_edit_text(self, text=None, **kwargs):
    CAPTURED.append({"kind": "edit", "text": text or "", "kwargs": kwargs, "self": self})
    return self


async def fake_edit_reply_markup(self, *args, **kwargs):
    return True


async def fake_document(self, *args, **kwargs):
    CAPTURED.append({"kind": "document", "text": "<doc>", "kwargs": kwargs, "self": self})
    return Message(message_id=1, date=datetime.now(), chat=self.chat, text="<doc>")


async def fake_get_chat_member(self, chat_id, user_id, *a, **kw):
    if user_id == ADMIN.id:
        return ChatMemberAdministrator(
            user=ADMIN, can_be_edited=False, is_anonymous=False, can_manage_chat=True,
            can_delete_messages=True, can_manage_video_chats=True, can_restrict_members=True,
            can_promote_members=True, can_change_info=True, can_invite_users=True,
            can_pin_messages=True, can_post_stories=False, can_edit_stories=False,
            can_delete_stories=False, can_send_welcome_messages=False,
        )
    return ChatMemberMember(user=MEMBER)


async def fake_get_chat(self, chat_id, *a, **kw):
    chat = Chat(id=chat_id if isinstance(chat_id, int) else -100, type="private",
                first_name="Member", username="member")
    return chat


async def fake_true(self, *a, **kw):
    return True


async def fake_count(self, chat_id, *a, **kw):
    return 7


async def fake_delete_on_bot(self, chat_id, message_id, *a, **kw):
    CAPTURED.append({"kind": "delete", "text": "<bot delete>", "kwargs": {}, "self": None})
    return True


async def fake_send_on_bot(self, chat_id, text=None, *a, **kw):
    CAPTURED.append({"kind": "send", "text": text or "", "kwargs": kw, "self": None})
    return Message(message_id=1, date=datetime.now(),
                   chat=Chat(id=chat_id, type="supergroup"), text=text or "")


async def make_bot() -> Bot:
    return Bot(token="123456:TESTTOKEN",
               default=DefaultBotProperties(parse_mode=ParseMode.HTML))


BOT_PATCHES = {
    "get_chat_member": fake_get_chat_member,
    "get_chat": fake_get_chat,
    "ban_chat_member": fake_true,
    "unban_chat_member": fake_true,
    "restrict_chat_member": fake_true,
    "delete_message": fake_delete_on_bot,
    "send_message": fake_send_on_bot,
    "pin_chat_message": fake_true,
    "unpin_chat_message": fake_true,
    "get_chat_member_count": fake_count,
    "set_chat_permissions": fake_true,
    "set_my_commands": fake_true,
}


def make_message(text: str, user: User = MEMBER, reply_to: Message | None = None,
                 message_id: int = 500, entities=None) -> Message:
    return Message(
        message_id=message_id, date=datetime.now(), chat=GROUP, from_user=user, text=text,
        reply_to_message=reply_to, entities=entities,
    )


def update(msg: Message) -> Update:
    return Update(update_id=1, message=msg)


async def main() -> None:
    tmp = tempfile.mkdtemp()
    i18n.load()
    await db.init(os.path.join(tmp, "dry.db"))
    await db.update_chat(GROUP.id, lang="my")

    bot = await make_bot()
    dp = Dispatcher()
    dp.message.outer_middleware(DisabledCommandMiddleware())
    dp.message.outer_middleware(register_chat_middleware)
    for router in (core.router, settings.router, moderation.router, antispam.router,
                   captcha.router, greetings.router, content.router, federation.router,
                   watcher.router):
        dp.include_router(router)

    patch_targets = [(Message, "reply", fake_reply), (Message, "answer", fake_answer),
                     (Message, "delete", fake_delete), (Message, "edit_text", fake_edit_text),
                     (Message, "edit_reply_markup", fake_edit_reply_markup),
                     (Message, "reply_document", fake_document)]
    patch_targets += [(Bot, name, func) for name, func in BOT_PATCHES.items()]
    stack = ExitStack()
    for target, name, func in patch_targets:
        stack.enter_context(patch.object(target, name, func))
    with stack:
        print("1) /help (မြန်မာ)")
        CAPTURED.clear()
        await dp.feed_update(bot, update(make_message("/help")))
        check("help ပြန်ပေးတယ်", "Command စာရင်း" in last_text(), last_text()[:120])

        print("2) /lang en")
        CAPTURED.clear()
        await dp.feed_update(bot, update(make_message("/lang en", ADMIN)))
        check("ဘာသာစကား ပြောင်းတယ်", (await db.get_chat(GROUP.id))["lang"] == "en")

        print("3) /setflood 4 (admin)")
        CAPTURED.clear()
        await dp.feed_update(bot, update(make_message("/setflood 4", ADMIN)))
        check("flood setting သိမ်းတယ်", (await db.get_chat(GROUP.id))["flood"] == 4, last_text()[:120])
        check("ပြန်ကြားတယ်", "Antiflood" in last_text())

        print("4) /ban member (admin → member)")
        CAPTURED.clear()
        target = make_message("spam", MEMBER, message_id=400)
        await dp.feed_update(bot, update(make_message("/ban", ADMIN, reply_to=target)))
        check("ban ပြန်ကြားတယ်", "ban" in last_text().lower(), last_text()[:120])

        print("5) /ban ကို သာမန် member ရိုက်ခြင်း")
        CAPTURED.clear()
        await dp.feed_update(bot, update(make_message("/ban", MEMBER, reply_to=target)))
        check("admin-only error", "admin" in last_text().lower(), last_text()[:120])

        print("6) /lock url → လင့်ခ်ပို့ခြင်း")
        CAPTURED.clear()
        await dp.feed_update(bot, update(make_message("/lock url", ADMIN)))
        check("lock သိမ်းတယ်", "url" in (await db.get_chat(GROUP.id))["locks"])
        CAPTURED.clear()
        from aiogram.types import MessageEntity

        spam = make_message("join https://spam.example now", MEMBER, message_id=501,
                            entities=[MessageEntity(type="url", offset=5, length=20)])
        await dp.feed_update(bot, update(spam))
        check("url message ဖျက်တယ်", any(c["kind"] == "delete" for c in CAPTURED), str(CAPTURED)[:200])

        print("7) blocklist")
        CAPTURED.clear()
        (await db.get_chat(GROUP.id))["locks"]
        await db.update_chat(GROUP.id, locks="[]")
        await dp.feed_update(bot, update(make_message("/addblocklist ငွေလဲ", ADMIN)))
        check("blocklist သိမ်းတယ်", "ငွေလဲ" in await db.list_blocks(GROUP.id))
        CAPTURED.clear()
        await dp.feed_update(bot, update(make_message("ဒီမှာ ငွေလဲပါတယ်", MEMBER, message_id=502)))
        check("blocklist message ဖျက်တယ်", any(c["kind"] == "delete" for c in CAPTURED))

        print("8) filters + notes")
        CAPTURED.clear()
        await dp.feed_update(bot, update(make_message("/filter price ဈေးနှုန်း 5000", ADMIN)))
        CAPTURED.clear()
        await dp.feed_update(bot, update(make_message("what is the price?", MEMBER, message_id=503)))
        check("filter ပြန်ဖြေတယ်", "5000" in last_text(), last_text()[:120])

        CAPTURED.clear()
        await dp.feed_update(bot, update(make_message("/save info ဒီ group က ရောင်းဝယ်ရေး group", ADMIN)))
        CAPTURED.clear()
        await dp.feed_update(bot, update(make_message("#info", MEMBER, message_id=504)))
        check("note ပြန်ဖြေတယ်", "ရောင်းဝယ်ရေး" in last_text(), last_text()[:120])

        print("9) /settings panel")
        CAPTURED.clear()
        await dp.feed_update(bot, update(make_message("/settings", ADMIN)))
        check("panel ပို့တယ်", "Settings" in last_text() and last_text() != "", last_text()[:100])
        check("inline button ပါတယ်", CAPTURED and CAPTURED[-1]["kwargs"].get("reply_markup") is not None)

        print("10) /captcha on")
        CAPTURED.clear()
        await dp.feed_update(bot, update(make_message("/captcha on", ADMIN)))
        chat = await db.get_chat(GROUP.id)
        check("captcha ဖွင့်တယ်", chat["captcha"] == 1 and chat["welcome_on"] == 1, str(chat["captcha"]))

        print("11) Member အသစ်ဝင်လာခြင်း (welcome + captcha)")
        CAPTURED.clear()
        newbie = User(id=333, is_bot=False, first_name="Newbie")
        join = Message(message_id=505, date=datetime.now(), chat=GROUP, from_user=newbie,
                       new_chat_members=[newbie])
        await dp.feed_update(bot, update(join))
        check("welcome/captcha ပို့တယ်", len(CAPTURED) >= 1, str(CAPTURED)[:200])
        check("captcha row ဖန်တီးတယ်", len(await db.all_captchas()) >= 1)

        print("12) /export")
        CAPTURED.clear()
        await dp.feed_update(bot, update(make_message("/export", ADMIN)))
        check("export file ပို့တယ်", any(c["kind"] == "document" for c in CAPTURED))

        print("13) /stats")
        CAPTURED.clear()
        await dp.feed_update(bot, update(make_message("/stats", ADMIN)))
        check("stats ပြန်တယ်", "Stats" in last_text(), last_text()[:120])

    await bot.session.close()
    await db.close()

    print()
    if FAILS:
        print(f"❌ {len(FAILS)} ခု မအောင်မြင်: {FAILS}")
        raise SystemExit(1)
    print("🎉 Dry-run အားလုံး အောင်မြင်ပါတယ်")


if __name__ == "__main__":
    asyncio.run(main())
