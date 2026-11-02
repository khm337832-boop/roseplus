"""tools/selfcheck.py — token မလိုဘဲ code အားလုံး အလုပ်လုပ်မလုပ် စမ်းသပ်တယ်။
run: python tools/selfcheck.py
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault("BOT_TOKEN", "000000:TESTTOKEN")

FAILS: list[str] = []


def check(name: str, condition: bool, extra: str = "") -> None:
    if condition:
        print(f"  ✅ {name}")
    else:
        FAILS.append(name)
        print(f"  ❌ {name} {extra}")


async def main() -> None:
    print("1) Module import တွေ စစ်ဆေးခြင်း")
    import i18n
    import db
    import helpers
    import common
    from plugins import (  # noqa: F401
        antispam, captcha, content, core, federation, greetings, moderation, settings, watcher,
    )
    import bot as bot_module  # noqa: F401

    print("2) Locale ဖိုင်တွေ")
    i18n.load()
    check("my, en နှစ်ခုလုံး တင်ပြီး", set(i18n.available()) == {"my", "en"}, str(i18n.available()))
    missing = i18n.missing_keys()
    check("key အားလုံး ညီတယ်", not missing, json.dumps(missing, ensure_ascii=False)[:400])
    check("t() fallback", i18n.t("my", "welcome_on").startswith("✅"))
    check("t() မသိတဲ့ key", i18n.t("my", "no_such_key_xyz") == "no_such_key_xyz")

    print("3) Helper တွေ")
    check("parse_time 10m", helpers.parse_time("10m") == 600)
    check("parse_time 2h", helpers.parse_time("2h") == 7200)
    check("parse_time 1d", helpers.parse_time("1d") == 86400)
    check("parse_time မမှန်", helpers.parse_time("abc") is None)
    check("human_time", helpers.human_time(600) == "10m", helpers.human_time(600))
    check("blocked_word ASCII boundary", helpers.blocked_word("hello scammer", ["scam"]) is None)
    check("blocked_word ASCII hit", helpers.blocked_word("you scam here", ["scam"]) == "scam")
    check("blocked_word မြန်မာ", helpers.blocked_word("ဒီမှာ ငွေလဲပါတယ်", ["ငွေလဲ"]) == "ငွေလဲ")
    text, markup = helpers.extract_buttons("Hi {first}\n[Website](buttonurl://https://example.com)")
    check("button ခွဲထုတ်ခြင်း", markup is not None and "buttonurl" not in text)

    print("4) Database CRUD (SQLite)")
    tmp = tempfile.mkdtemp()
    await db.init(os.path.join(tmp, "test.db"))
    chat = await db.get_chat(-100123)
    check("chat default ဖန်တီး", chat["lang"] == "my" and chat["warn_limit"] == 3)
    await db.update_chat(-100123, flood=5, welcome_on=1)
    chat = await db.get_chat(-100123)
    check("update_chat", chat["flood"] == 5 and chat["welcome_on"] == 1)
    check("warn တင်ခြင်း", await db.add_warn(-100123, 42, "spam") == 1)
    check("warn ထပ်တင်ခြင်း", await db.add_warn(-100123, 42, "spam2") == 2)
    check("count_warns", await db.count_warns(-100123) == 1)
    await db.reset_warns(-100123, 42)
    check("reset_warns", await db.get_warn(-100123, 42) == (0, []))
    await db.add_block(-100123, "ငွေလဲ")
    check("blocklist", await db.list_blocks(-100123) == ["ငွေလဲ"])
    await db.save_note(-100123, "info", "<b>မင်္ဂလာပါ</b>")
    check("note", await db.get_note(-100123, "INFO") == "<b>မင်္ဂလာပါ</b>")
    await db.set_filter(-100123, "price", "5000 ks", 1, 0)
    check("filter", (await db.get_filter(-100123, "price"))["admin_only"] == 1)
    await db.approve(-100123, 42)
    check("approvals", await db.is_approved(-100123, 42))
    await db.add_captcha(-100123, 7, 0, "9")
    check("captcha row", len(await db.all_captchas()) == 1)
    await db.create_fed("abcd1234", "TestFed", 99)
    await db.join_fed(-100123, "abcd1234")
    check("federation", (await db.chat_fed(-100123))["name"] == "TestFed")
    await db.fed_ban("abcd1234", 5, "spam", 99)
    check("fed ban", await db.is_fed_banned("abcd1234", 5))
    await db.close()

    print("5) Antiflood engine")
    settings_dict = {"flood": 3, "flood_win": 0, "flood_win_seconds": 10, "clearflood": 0}
    results = [antispam.flood_register(-100999, 11, i, settings_dict)[0] for i in range(1, 4)]
    check("flood limit 3 မှာ တတိယမြောက် trigger", results == [False, False, True], str(results))
    settings_dict2 = {"flood": 0, "flood_win": 2, "flood_win_seconds": 10, "clearflood": 1}
    r1 = antispam.flood_register(-100998, 12, 1, settings_dict2)
    r2 = antispam.flood_register(-100998, 12, 2, settings_dict2)
    check("window flood + clearflood", r2[0] and len(r2[1]) == 2, str(r2))

    print("6) Lock detection")
    from datetime import datetime

    from aiogram.types import Chat, Message, MessageEntity

    msg = Message(
        message_id=1, date=datetime.now(), chat=Chat(id=-1, type="supergroup"),
        text="see https://spam.example",
        entities=[MessageEntity(type="url", offset=4, length=21)],
    )
    check("url lock ဖမ်းမိ", "url" in helpers.detect_lock_types(msg), str(helpers.detect_lock_types(msg)))

    print()
    if FAILS:
        print(f"❌ {len(FAILS)} ခု မအောင်မြင်ပါ: {FAILS}")
        raise SystemExit(1)
    print("🎉 အားလုံး အောင်မြင်ပါတယ်")


if __name__ == "__main__":
    asyncio.run(main())
