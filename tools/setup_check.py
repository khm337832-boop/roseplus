"""tools/setup_check.py — token နဲ့ setting တွေ မှန်/မမှန် စစ်ဆေးတယ်။
run: python tools/setup_check.py

ဒီ script က .env ထဲက token ကို အသုံးပြုတာမို့ token ကို ဘယ်သူ့ကိုမှ ပေးစရာ မလိုပါ။
"""
from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

FAILS: list[str] = []


def ok(text: str) -> None:
    print(f"  ✅ {text}")


def bad(text: str) -> None:
    FAILS.append(text)
    print(f"  ❌ {text}")


def warn(text: str) -> None:
    print(f"  ⚠️  {text}")


async def main() -> None:
    import config

    print("1) .env / token စစ်ဆေးခြင်း")
    if not config.BOT_TOKEN:
        bad(".env ထဲမှာ BOT_TOKEN မရှိပါ — `.env.example` ကို `.env` အဖြစ် copy ပြီး ထည့်ပါ")
        return
    if ":" not in config.BOT_TOKEN or not config.BOT_TOKEN.split(":")[0].isdigit():
        bad("BOT_TOKEN ပုံစံ မမှန်ပါ (123456789:AAH… ပုံစံ ဖြစ်ရမယ်)")
        return
    ok(f"token ပုံစံ မှန်တယ် ({config.BOT_TOKEN[:8]}…{config.BOT_TOKEN[-4:]})")
    ok(f"default language: {config.DEFAULT_LANG}")

    from aiogram import Bot
    from aiogram.exceptions import TelegramUnauthorizedError

    print("\n2) Telegram နဲ့ ချိတ်ဆက်ခြင်း (getMe)")
    bot = Bot(token=config.BOT_TOKEN)
    try:
        me = await bot.get_me()
    except TelegramUnauthorizedError:
        bad("token မမှန်ပါ (သို့) bot ကို ဖျက်ထားပါတယ် — BotFather မှာ /mybots နဲ့ ပြန်စစ်ပါ")
        await bot.session.close()
        return
    except Exception as exc:  # network
        bad(f"Telegram နဲ့ မချိတ်နိုင်ပါ ({type(exc).__name__}) — internet/VPN စစ်ပါ")
        await bot.session.close()
        return
    ok(f"bot: @{me.username}  (id: {me.id})")
    ok(f"အမည်: {me.full_name}")

    print("\n3) Privacy mode (locks / blocklist / filters အတွက် အရေးကြီး)")
    if me.can_read_all_group_messages:
        ok("privacy mode ပိတ်ထားတယ် — message အားလုံး ဖတ်နိုင်မယ်")
    else:
        bad("privacy mode ဖွင့်နေတယ် → BotFather → /setprivacy → Disable လုပ်ပါ\n"
            "     (မပိတ်ရင် locks / blocklist / filters အလုပ်မလုပ်ပါ)")
    if me.can_join_groups:
        ok("group ထဲ ထည့်လို့ ရနိုင်တယ်")
    else:
        bad("group ထဲ ထည့်ခွင့် မရှိပါ (BotFather → /setjoingroups → Enable)")

    print("\n4) Webhook / polling")
    try:
        info = await bot.get_webhook_info()
        if info.url:
            warn(f"webhook တင်ထားတယ်: {info.url}\n"
                 f"     polling နဲ့ run မယ်ဆိုရင် /deleteWebhook လို bot API ကို ခေါ်ရမယ် "
                 f"(ဒီ script က ဖျက်မပေးပါ)")
        else:
            ok("webhook မရှိပါ — polling နဲ့ run လို့ ရတယ်")
    except Exception as exc:
        warn(f"webhook အခြေအနေ မစစ်နိုင်ပါ ({type(exc).__name__})")

    print("\n5) Database")
    import db

    await db.init(config.DB_PATH)
    chat = await db.get_chat(-100999)
    await db.update_chat(-100999, flood=5)
    again = await db.get_chat(-100999)
    if again["flood"] == 5:
        ok(f"SQLite ရေးနိုင်/ဖတ်နိုင်တယ် → {config.DB_PATH}")
    else:
        bad("database ရေးလို့ မရပါ — folder permission စစ်ပါ")
    await db.close()
    await bot.session.close()

    print("\n6) နောက်လုပ်ရမယ့် အဆင့်များ")
    print(f"  ➤ ./run.sh  (သို့) python bot.py")
    print(f"  ➤ Telegram မှာ @{me.username} ကို သင့် group ထဲ ထည့်ပြီး **admin right အားလုံး** ပေးပါ")
    print(f"  ➤ group ထဲမှာ /settings ရိုက်ပြီး စမ်းပါ")
    print(f"  ➤ link: https://t.me/{me.username}?startgroup=botstart")

    print()
    if FAILS:
        print(f"❌ {len(FAILS)} ချက် မအောင်မြင်ပါ — အပေါ်မှာ ပြင်ပြီး ထပ်စမ်းပါ")
        raise SystemExit(1)
    print("🎉 အားလုံး အဆင်သင့် ဖြစ်ပါပြီ — bot ကို run လို့ ရပါပြီ")


if __name__ == "__main__":
    asyncio.run(main())
