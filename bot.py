"""
Goii Auto Bot — မြန်မာ/English နှစ်ဘာသာ group management bot
run:  python bot.py
"""
from __future__ import annotations

import asyncio
import json
import os
import logging
import sys

from aiogram import Bot, Dispatcher, F, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.dispatcher.event.bases import CancelHandler
from aiogram.enums import ParseMode
from aiogram.types import BotCommand, Message

import config
import db
import i18n
from plugins import (
    antispam,
    captcha,
    content,
    core,
    federation,
    gate,
    greetings,
    menu,
    moderation,
    settings,
    watcher,
)

log = logging.getLogger("goii")

COMMANDS = [
    BotCommand(command="menu", description="🌸 Button menu (အလွယ်ဆုံး)"),
    BotCommand(command="quick", description="🚀 ၄ ဆင့်နဲ့ အသင့်ဖြစ်အောင်"),
    BotCommand(command="help", description="Command စာရင်း / command list"),
    BotCommand(command="settings", description="⚙️ Settings panel"),
    BotCommand(command="lang", description="🌐 my | en"),
    BotCommand(command="ban", description="Ban a user"),
    BotCommand(command="mute", description="Mute a user"),
    BotCommand(command="warn", description="Warn a user"),
    BotCommand(command="lock", description="Lock content types"),
    BotCommand(command="captcha", description="CAPTCHA on|off"),
    BotCommand(command="setwelcome", description="Welcome message"),
    BotCommand(command="save", description="Save a note"),
    BotCommand(command="rules", description="Show group rules"),
    BotCommand(command="id", description="Show chat/user id"),
]


class DisabledCommandMiddleware:
    """admin တွေ /disable လုပ်ထားတဲ့ command ကို ပိတ်တယ်။"""

    async def __call__(self, handler, event: Message, data):
        if isinstance(event, Message) and event.text and event.text.startswith("/"):
            command = event.text.split()[0][1:].split("@")[0].lower()
            if event.chat.type in ("group", "supergroup"):
                chat = await db.get_chat(event.chat.id)
                disabled = json.loads(chat.get("disabled") or "[]")
                if command in disabled:
                    raise CancelHandler()
        return await handler(event, data)


async def register_chat_middleware(handler, event: Message, data):
    """Chat/user အသစ်တွေကို database မှာ အလိုအလျောက် မှတ်တယ်။"""
    try:
        if event.chat.type in ("group", "supergroup"):
            chat = await db.get_chat(event.chat.id)
            if chat.get("title") != (event.chat.title or ""):
                await db.update_chat(event.chat.id, title=event.chat.title or "")
        if event.from_user and not event.from_user.is_bot:
            await db.touch_user(event.from_user.id, event.chat.type == "private"
                                and config.DEFAULT_LANG or config.DEFAULT_LANG)
    except Exception:
        log.exception("middleware error")
    return await handler(event, data)


async def on_error(event) -> bool:
    log.error("handler error: %s", getattr(event, "exception", event))
    return True


async def start_health_server() -> asyncio.AbstractServer | None:
    """Render / Railway စတဲ့ PaaS တွေက HTTP port ဖွင့်ထားမှ free tier ပေးတယ်။
    PORT env ရှိရင်သာ run မယ် (local မှာ မလို)။"""
    port = os.getenv("PORT")
    if not port:
        return None

    async def handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            await asyncio.wait_for(reader.read(2048), timeout=5)
            body = b"Goii Auto Bot is alive"
            writer.write(
                b"HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\n"
                b"Content-Length: " + str(len(body)).encode() + b"\r\nConnection: close\r\n\r\n" + body
            )
            await writer.drain()
        except Exception:
            pass
        finally:
            try:
                writer.close()
            except Exception:
                pass

    server = await asyncio.start_server(handle, "0.0.0.0", int(port))
    log.info("🌐 health server listening on 0.0.0.0:%s (for Render/Railway)", port)
    return server


async def main() -> None:
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    )
    if not config.BOT_TOKEN or ":" not in config.BOT_TOKEN:
        print("❌ BOT_TOKEN မရှိပါ။ .env ဖိုင်မှာ BOT_TOKEN=... ထည့်ပါ။\n"
              "   Get one from @BotFather in Telegram.", file=sys.stderr)
        raise SystemExit(1)

    i18n.load()
    await db.init(config.DB_PATH)

    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML,
                                     link_preview_is_disabled=True),
    )
    dp = Dispatcher()

    # middleware
    if config.force_sub_enabled():
        dp.message.outer_middleware(gate.ForceJoinMiddleware())
        dp.callback_query.outer_middleware(gate.ForceJoinMiddleware())
    dp.message.outer_middleware(DisabledCommandMiddleware())
    dp.message.outer_middleware(register_chat_middleware)

    # router အစဉ်လိုက် — watcher က နောက်ဆုံး
    for router in (gate.router, core.router, menu.router, settings.router, moderation.router, antispam.router,
                   captcha.router, greetings.router, content.router, federation.router,
                   watcher.router):
        dp.include_router(router)

    dp.errors.register(on_error)

    # background job — CAPTCHA အချိန်ကုန်တာတွေ စစ်
    asyncio.create_task(captcha.expiry_worker(bot))
    health_server = await start_health_server()

    me = await bot.get_me()
    await bot.set_my_commands(COMMANDS)
    log.info("🤖 Goii Auto Bot started as @%s (%s)", me.username, me.id)
    log.info("   Default language: %s | DB backend: %s", config.DEFAULT_LANG, db.backend_name())
    if config.force_sub_enabled():
        log.info("   Force-join: %s (မဝင်ရင် bot ကို မသုံးနိုင်)", config.FORCE_SUB_CHANNEL)

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        if health_server is not None:
            health_server.close()
        await bot.session.close()
        await db.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
