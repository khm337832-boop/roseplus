"""tools/db_check.py — Database (SQLite သို့ Postgres) အားလုံး အလုပ်လုပ်မလုပ် စမ်းသပ်တယ်။
run: python tools/db_check.py

- DATABASE_URL မထည့်ထားရင် → SQLite (data/roseplus.db) ကို စမ်းတယ်
- DATABASE_URL ထည့်ထားရင် → အဲ့ Postgres (Supabase/Neon) ကို တကယ် စမ်းတယ်
  ↑ Render မှာ deploy မလုပ်ခင် ကိုယ့်ကွန်ပျူတာကနေ ဒါကို run ပြီး စစ်နိုင်တယ်
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAILS: list[str] = []


def check(name: str, cond: bool, extra: str = "") -> None:
    print(("  ✅ " if cond else "  ❌ ") + name + ("" if cond else f"  {extra}"))
    if not cond:
        FAILS.append(name)


CMDS: list[str] = []


async def exercise() -> None:
    """db.init() ပြီးသား backend ပေါ်မှာ function အားလုံးကို စမ်းတယ်။"""
    import db

    chat_id, user_id = -1009988776655, 777000111

    print("1) chats")
    chat = await db.get_chat(chat_id)
    check("ဖန်တီးတယ် / default ရတယ်", chat.get("lang") == "my" and chat.get("warn_limit") == 3, str(chat)[:150])
    await db.update_chat(chat_id, flood=5, welcome_on=1, title="Test Group")
    chat = await db.get_chat(chat_id)
    check("update_chat", chat["flood"] == 5 and chat["welcome_on"] == 1)
    await db.bump_messages(chat_id)
    check("bump_messages", (await db.get_chat(chat_id))["msg_count"] >= 1)

    print("2) users")
    await db.set_user_lang(user_id, "en")
    check("set/get user lang", await db.get_user_lang(user_id) == "en")

    print("3) warns")
    check("warn 1", await db.add_warn(chat_id, user_id, "spam") == 1)
    check("warn 2", await db.add_warn(chat_id, user_id, "spam2") == 2)
    check("count_warns", await db.count_warns(chat_id) == 1)
    count, reasons = await db.get_warn(chat_id, user_id)
    check("get_warn", count == 2 and len(reasons) == 2, str(reasons))
    check("remove_warn", await db.remove_warn(chat_id, user_id) == 1)
    await db.reset_warns(chat_id, user_id)
    check("reset_warns", await db.get_warn(chat_id, user_id) == (0, []))

    print("4) blocklist")
    check("add_block", await db.add_block(chat_id, "ငွေလဲ"))
    check("add_block (duplicate → False)", not await db.add_block(chat_id, "ငွေလဲ"))
    check("list_blocks", await db.list_blocks(chat_id) == ["ငွေလဲ"])
    await db.del_block(chat_id, "ငွေလဲ")
    check("del_block", await db.list_blocks(chat_id) == [])

    print("5) notes / filters")
    await db.save_note(chat_id, "info", "<b>မင်္ဂလာပါ</b>")
    check("note save/get", await db.get_note(chat_id, "INFO") == "<b>မင်္ဂလာပါ</b>")
    check("note list", await db.list_notes(chat_id) == ["info"])
    await db.set_filter(chat_id, "price", "5000 ks", 1, 0)
    check("filter set/get", (await db.get_filter(chat_id, "price"))["admin_only"] == 1)
    check("filter list", len(await db.list_filters(chat_id)) == 1)
    await db.del_filter(chat_id, "price")
    check("filter del", await db.get_filter(chat_id, "price") is None)

    print("6) approvals / captcha")
    await db.approve(chat_id, user_id)
    check("approve", await db.is_approved(chat_id, user_id))
    await db.unapprove(chat_id, user_id)
    check("unapprove", not await db.is_approved(chat_id, user_id))
    await db.add_captcha(chat_id, user_id, 0, "9")
    check("captcha add", len(await db.all_captchas()) >= 1)
    await db.del_captcha(chat_id, user_id)
    check("captcha del", len([c for c in await db.all_captchas() if c["user_id"] == user_id]) == 0)

    print("7) federation")
    await db.create_fed("test1234", "TestFed", user_id)
    await db.join_fed(chat_id, "test1234")
    fed = await db.chat_fed(chat_id)
    check("fed create/join", fed is not None and fed["fed_id"] == "test1234")
    await db.fed_ban("test1234", 12345, "spam", user_id)
    check("fed ban", await db.is_fed_banned("test1234", 12345))
    check("fed ban list", len(await db.fed_ban_list("test1234")) == 1)
    await db.fed_unban("test1234", 12345)
    check("fed unban", not await db.is_fed_banned("test1234", 12345))
    await db.leave_fed(chat_id)
    check("leave fed", await db.chat_fed(chat_id) is None)

    print("8) all_chats")
    check("all_chats", len(await db.all_chats()) >= 1)

    print()


async def main() -> None:
    import config  # noqa: F401  (.env ဖတ်ဖို့)
    import db

    if db.DATABASE_URL:
        backend = await db.init()
    else:
        import tempfile

        backend = await db.init(os.path.join(tempfile.mkdtemp(), "check.db"))
    print(f"backend: {backend}")
    if db.DATABASE_URL:
        safe_url = db.DATABASE_URL.split("@")[-1]
        print(f"target : …@{safe_url}\n")
    else:
        print(f"target : {db.DB_PATH}\n")

    await exercise()
    await db.close()
    if FAILS:
        print(f"❌ {len(FAILS)} ခု မအောင်မြင်: {FAILS}")
        raise SystemExit(1)
    print(f"🎉 Database ({backend}) အားလုံး အောင်မြင်ပါတယ်")


if __name__ == "__main__":
    asyncio.run(main())
