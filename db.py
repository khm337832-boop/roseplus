"""
db.py — SQLite (aiosqlite) အခြေခံ data layer
External database မလိုအပ်ဘဲ အခမဲ့ run နိုင်အောင် SQLite ကို သုံးထားပါတယ်။
Volume/disk တစ်ခုပေါ်မှာ file တစ်ခုတည်း သိမ်းရုံပါ။
"""
from __future__ import annotations

import json
import os
import time
from typing import Any, Iterable

import aiosqlite

DB_PATH = os.getenv("DB_PATH", "data/roseplus.db")
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

_backend = None

SCHEMA = """
CREATE TABLE IF NOT EXISTS chats (
    chat_id           BIGINT PRIMARY KEY,
    title             TEXT    DEFAULT '',
    lang              TEXT    DEFAULT 'my',
    welcome           TEXT    DEFAULT '',
    welcome_on        INTEGER DEFAULT 0,
    goodbye           TEXT    DEFAULT '',
    goodbye_on        INTEGER DEFAULT 0,
    cleanwelcome      INTEGER DEFAULT 0,
    cleanservice      INTEGER DEFAULT 0,
    rules             TEXT    DEFAULT '',
    rules_private     INTEGER DEFAULT 0,
    flood             INTEGER DEFAULT 0,
    flood_mode        TEXT    DEFAULT 'mute',
    flood_win         INTEGER DEFAULT 0,
    flood_win_seconds INTEGER DEFAULT 10,
    clearflood        INTEGER DEFAULT 0,
    warn_limit        INTEGER DEFAULT 3,
    warn_mode         TEXT    DEFAULT 'ban',
    warn_expiry       INTEGER DEFAULT 0,
    captcha           INTEGER DEFAULT 0,
    captcha_mode      TEXT    DEFAULT 'button',
    captcha_kick      INTEGER DEFAULT 0,
    captcha_kick_time INTEGER DEFAULT 300,
    captcha_rules     INTEGER DEFAULT 0,
    captcha_text      TEXT    DEFAULT '',
    antiraid          INTEGER DEFAULT 0,
    antiraid_time     INTEGER DEFAULT 3600,
    antiraid_limit    INTEGER DEFAULT 8,
    locks             TEXT    DEFAULT '[]',
    disabled          TEXT    DEFAULT '[]',
    blocklist_mode    TEXT    DEFAULT 'delete',
    log_channel       BIGINT DEFAULT 0,
    msg_count         INTEGER DEFAULT 0,
    created_at        INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS users (
    user_id    BIGINT PRIMARY KEY,
    lang       TEXT DEFAULT 'my',
    first_seen INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS warns (
    chat_id  BIGINT,
    user_id  BIGINT,
    count    INTEGER DEFAULT 0,
    reasons  TEXT    DEFAULT '[]',
    updated  INTEGER DEFAULT 0,
    PRIMARY KEY (chat_id, user_id)
);

CREATE TABLE IF NOT EXISTS blocklist (
    chat_id BIGINT,
    word    TEXT,
    PRIMARY KEY (chat_id, word)
);

CREATE TABLE IF NOT EXISTS filters (
    chat_id    BIGINT,
    trigger    TEXT,
    reply      TEXT,
    admin_only INTEGER DEFAULT 0,
    protect    INTEGER DEFAULT 0,
    PRIMARY KEY (chat_id, trigger)
);

CREATE TABLE IF NOT EXISTS notes (
    chat_id BIGINT,
    name    TEXT,
    content TEXT,
    PRIMARY KEY (chat_id, name)
);

CREATE TABLE IF NOT EXISTS approvals (
    chat_id BIGINT,
    user_id BIGINT,
    PRIMARY KEY (chat_id, user_id)
);

CREATE TABLE IF NOT EXISTS captchas (
    chat_id  BIGINT,
    user_id  BIGINT,
    until    INTEGER DEFAULT 0,
    answer   TEXT    DEFAULT '',
    PRIMARY KEY (chat_id, user_id)
);

CREATE TABLE IF NOT EXISTS feds (
    fed_id    TEXT PRIMARY KEY,
    name      TEXT,
    owner_id  BIGINT,
    created   INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS fed_chats (
    chat_id BIGINT PRIMARY KEY,
    fed_id  TEXT,
    joined  INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS fed_bans (
    fed_id   TEXT,
    user_id  BIGINT,
    reason   TEXT DEFAULT '',
    by_id    BIGINT DEFAULT 0,
    at       INTEGER DEFAULT 0,
    PRIMARY KEY (fed_id, user_id)
);
"""

# chats table ထဲ ပြောင်းလို့ရတဲ့ column စာရင်း (SQL injection ကာကွယ်ဖို့ whitelist)
CHAT_FIELDS = {
    "title", "lang", "welcome", "welcome_on", "goodbye", "goodbye_on",
    "cleanwelcome", "cleanservice", "rules", "rules_private",
    "flood", "flood_mode", "flood_win", "flood_win_seconds", "clearflood",
    "warn_limit", "warn_mode", "warn_expiry",
    "captcha", "captcha_mode", "captcha_kick", "captcha_kick_time",
    "captcha_rules", "captcha_text",
    "antiraid", "antiraid_time", "antiraid_limit",
    "locks", "disabled", "blocklist_mode", "log_channel", "msg_count",
}


class _SQLiteBackend:
    """Default backend — file တစ်ခုတည်း၊ server မလို (local / VPS / Docker)။"""

    name = "sqlite"

    def __init__(self, path: str) -> None:
        self.path = path
        self.conn: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        directory = os.path.dirname(os.path.abspath(self.path))
        if directory:
            os.makedirs(directory, exist_ok=True)
        self.conn = await aiosqlite.connect(self.path)
        self.conn.row_factory = aiosqlite.Row
        await self.conn.execute("PRAGMA journal_mode=WAL")
        await self.conn.execute("PRAGMA busy_timeout=10000")
        await self.conn.execute("PRAGMA synchronous=NORMAL")
        await self.conn.executescript(SCHEMA)
        await self.conn.commit()

    async def fetchone(self, sql: str, params) -> dict | None:
        async with self.conn.execute(sql, tuple(params)) as cur:
            row = await cur.fetchone()
        return dict(row) if row else None

    async def fetchall(self, sql: str, params) -> list[dict]:
        async with self.conn.execute(sql, tuple(params)) as cur:
            rows = await cur.fetchall()
        return [dict(r) for r in rows]

    async def execute(self, sql: str, params) -> None:
        await self.conn.execute(sql, tuple(params))
        await self.conn.commit()

    async def close(self) -> None:
        if self.conn is not None:
            await self.conn.close()
            self.conn = None


class _PostgresBackend:
    """DATABASE_URL ထည့်ထားရင် (Render / Railway / Supabase / Neon) ဒါကို သုံးတယ်။
    Free web host တွေမှာ disk မရှိတာမို့ data မပျောက်အောင် Postgres သုံးတာ အကောင်းဆုံး။"""

    name = "postgres"

    def __init__(self, dsn: str) -> None:
        self.dsn = dsn
        self.pool = None

    @staticmethod
    def _sql(sql: str) -> str:
        """`?` placeholder တွေကို `$1, $2 …` အဖြစ် ပြောင်း (asyncpg လိုအပ်ချက်)။"""
        out, index, in_single, in_double = [], 0, False, False
        for ch in sql:
            if ch == "'" and not in_double:
                in_single = not in_single
            elif ch == '"' and not in_single:
                in_double = not in_double
            if ch == "?" and not in_single and not in_double:
                index += 1
                out.append(f"${index}")
            else:
                out.append(ch)
        return "".join(out)

    async def connect(self) -> None:
        import asyncpg  # optional dependency

        self.pool = await asyncpg.create_pool(
            self.dsn, min_size=1, max_size=5, statement_cache_size=0,
            command_timeout=30,
        )
        async with self.pool.acquire() as conn:
            for statement in [x.strip() for x in SCHEMA.split(";") if x.strip()]:
                await conn.execute(statement)

    async def fetchone(self, sql: str, params) -> dict | None:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(self._sql(sql), *params)
        return dict(row) if row else None

    async def fetchall(self, sql: str, params) -> list[dict]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(self._sql(sql), *params)
        return [dict(r) for r in rows]

    async def execute(self, sql: str, params) -> None:
        async with self.pool.acquire() as conn:
            await conn.execute(self._sql(sql), *params)

    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.close()
            self.pool = None


async def init(path: str | None = None) -> str:
    """Database ချိတ်ဆက် + table ဖန်တီး။ သုံးနေတဲ့ backend အမည် ("sqlite"/"postgres") ပြန်ပေးတယ်။"""
    global _backend
    if DATABASE_URL.startswith(("postgres://", "postgresql://")) and path is None:
        _backend = _PostgresBackend(DATABASE_URL)
    else:
        _backend = _SQLiteBackend(path or DB_PATH)
    await _backend.connect()
    return _backend.name


async def close() -> None:
    global _backend
    if _backend is not None:
        await _backend.close()
        _backend = None


def backend_name() -> str:
    return getattr(_backend, "name", "unknown")


async def _fetchone(sql: str, params: Iterable[Any] = ()) -> dict | None:
    return await _backend.fetchone(sql, params)


async def _fetchall(sql: str, params: Iterable[Any] = ()) -> list[dict]:
    return await _backend.fetchall(sql, params)


async def _exec(sql: str, params: Iterable[Any] = ()) -> None:
    await _backend.execute(sql, params)


# ---------------------------------------------------------------- chats
async def get_chat(chat_id: int) -> dict:
    """Chat setting ကို ယူ; မရှိသေးရင် default နဲ့ ဖန်တီး။"""
    row = await _fetchone("SELECT * FROM chats WHERE chat_id = ?", (chat_id,))
    if row is None:
        await _exec(
            "INSERT INTO chats (chat_id, created_at) VALUES (?, ?) ON CONFLICT DO NOTHING",
            (chat_id, int(time.time())),
        )
        row = await _fetchone("SELECT * FROM chats WHERE chat_id = ?", (chat_id,))
    return dict(row) if row else {}


async def update_chat(chat_id: int, **fields: Any) -> None:
    clean = {k: v for k, v in fields.items() if k in CHAT_FIELDS}
    if not clean:
        return
    await get_chat(chat_id)
    sets = ", ".join(f"{k} = ?" for k in clean)
    await _exec(f"UPDATE chats SET {sets} WHERE chat_id = ?", (*clean.values(), chat_id))


async def all_chats() -> list[dict]:
    return [dict(r) for r in await _fetchall("SELECT * FROM chats")]


async def bump_messages(chat_id: int) -> None:
    await get_chat(chat_id)
    await _exec("UPDATE chats SET msg_count = msg_count + 1 WHERE chat_id = ?", (chat_id,))


# ---------------------------------------------------------------- users
async def get_user_lang(user_id: int) -> str | None:
    row = await _fetchone("SELECT lang FROM users WHERE user_id = ?", (user_id,))
    return row["lang"] if row else None


async def set_user_lang(user_id: int, lang: str) -> None:
    await _exec(
        "INSERT INTO users (user_id, lang, first_seen) VALUES (?, ?, ?) "
        "ON CONFLICT(user_id) DO UPDATE SET lang = excluded.lang",
        (user_id, lang, int(time.time())),
    )


async def touch_user(user_id: int, lang: str) -> None:
    await _exec(
        "INSERT INTO users (user_id, lang, first_seen) VALUES (?, ?, ?) "
        "ON CONFLICT DO NOTHING",
        (user_id, lang, int(time.time())),
    )


# ---------------------------------------------------------------- warns
async def add_warn(chat_id: int, user_id: int, reason: str, expiry: int = 0) -> int:
    if expiry:
        cutoff = int(time.time()) - expiry
        await _exec(
            "DELETE FROM warns WHERE chat_id = ? AND user_id = ? AND updated < ?",
            (chat_id, user_id, cutoff),
        )
    row = await _fetchone(
        "SELECT count, reasons, updated FROM warns WHERE chat_id = ? AND user_id = ?",
        (chat_id, user_id),
    )
    if row is None:
        count, reasons = 1, [reason]
        await _exec(
            "INSERT INTO warns (chat_id, user_id, count, reasons, updated) VALUES (?, ?, ?, ?, ?)",
            (chat_id, user_id, count, json.dumps(reasons, ensure_ascii=False), int(time.time())),
        )
    else:
        count = row["count"] + 1
        reasons = json.loads(row["reasons"] or "[]") + [reason]
        await _exec(
            "UPDATE warns SET count = ?, reasons = ?, updated = ? WHERE chat_id = ? AND user_id = ?",
            (count, json.dumps(reasons, ensure_ascii=False), int(time.time()), chat_id, user_id),
        )
    return count


async def get_warn(chat_id: int, user_id: int) -> tuple[int, list[str]]:
    row = await _fetchone(
        "SELECT count, reasons FROM warns WHERE chat_id = ? AND user_id = ?", (chat_id, user_id)
    )
    if not row:
        return 0, []
    return row["count"], json.loads(row["reasons"] or "[]")


async def remove_warn(chat_id: int, user_id: int) -> int:
    count, reasons = await get_warn(chat_id, user_id)
    if count <= 0:
        return 0
    count -= 1
    reasons = reasons[:-1] if reasons else []
    if count == 0:
        await _exec("DELETE FROM warns WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
    else:
        await _exec(
            "UPDATE warns SET count = ?, reasons = ?, updated = ? WHERE chat_id = ? AND user_id = ?",
            (count, json.dumps(reasons, ensure_ascii=False), int(time.time()), chat_id, user_id),
        )
    return count


async def count_warns(chat_id: int) -> int:
    row = await _fetchone(
        "SELECT COUNT(*) AS c FROM warns WHERE chat_id = ? AND count > 0", (chat_id,)
    )
    return int(row["c"]) if row else 0


async def reset_warns(chat_id: int, user_id: int) -> None:
    await _exec("DELETE FROM warns WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))


# ---------------------------------------------------------------- blocklist
async def add_block(chat_id: int, word: str) -> bool:
    try:
        await _exec("INSERT INTO blocklist (chat_id, word) VALUES (?, ?)", (chat_id, word))
        return True
    except Exception:  # unique constraint (SQLite/Postgres နှစ်မျိုးလုံး)
        return False


async def del_block(chat_id: int, word: str) -> bool:
    await _exec("DELETE FROM blocklist WHERE chat_id = ? AND word = ?", (chat_id, word))
    return True


async def clear_blocks(chat_id: int) -> None:
    await _exec("DELETE FROM blocklist WHERE chat_id = ?", (chat_id,))


async def list_blocks(chat_id: int) -> list[str]:
    rows = await _fetchall("SELECT word FROM blocklist WHERE chat_id = ? ORDER BY word", (chat_id,))
    return [r["word"] for r in rows]


# ---------------------------------------------------------------- filters
async def set_filter(chat_id: int, trigger: str, reply: str, admin_only: int = 0, protect: int = 0) -> None:
    await _exec(
        "INSERT INTO filters (chat_id, trigger, reply, admin_only, protect) VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(chat_id, trigger) DO UPDATE SET reply = excluded.reply, "
        "admin_only = excluded.admin_only, protect = excluded.protect",
        (chat_id, trigger, reply, admin_only, protect),
    )


async def get_filter(chat_id: int, trigger: str) -> dict | None:
    row = await _fetchone(
        "SELECT * FROM filters WHERE chat_id = ? AND trigger = ?", (chat_id, trigger)
    )
    return dict(row) if row else None


async def list_filters(chat_id: int) -> list[dict]:
    return [dict(r) for r in await _fetchall("SELECT * FROM filters WHERE chat_id = ?", (chat_id,))]


async def del_filter(chat_id: int, trigger: str) -> bool:
    await _exec("DELETE FROM filters WHERE chat_id = ? AND trigger = ?", (chat_id, trigger))
    return True


# ---------------------------------------------------------------- notes
async def save_note(chat_id: int, name: str, content: str) -> None:
    await _exec(
        "INSERT INTO notes (chat_id, name, content) VALUES (?, ?, ?) "
        "ON CONFLICT(chat_id, name) DO UPDATE SET content = excluded.content",
        (chat_id, name.lower(), content),
    )


async def get_note(chat_id: int, name: str) -> str | None:
    row = await _fetchone(
        "SELECT content FROM notes WHERE chat_id = ? AND name = ?", (chat_id, name.lower())
    )
    return row["content"] if row else None


async def list_notes(chat_id: int) -> list[str]:
    rows = await _fetchall("SELECT name FROM notes WHERE chat_id = ? ORDER BY name", (chat_id,))
    return [r["name"] for r in rows]


async def del_note(chat_id: int, name: str) -> bool:
    await _exec("DELETE FROM notes WHERE chat_id = ? AND name = ?", (chat_id, name.lower()))
    return True


# ---------------------------------------------------------------- approvals (whitelist)
async def approve(chat_id: int, user_id: int) -> None:
    await _exec("INSERT INTO approvals (chat_id, user_id) VALUES (?, ?) ON CONFLICT DO NOTHING", (chat_id, user_id))


async def unapprove(chat_id: int, user_id: int) -> None:
    await _exec("DELETE FROM approvals WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))


async def is_approved(chat_id: int, user_id: int) -> bool:
    row = await _fetchone(
        "SELECT 1 FROM approvals WHERE chat_id = ? AND user_id = ?", (chat_id, user_id)
    )
    return row is not None


async def list_approved(chat_id: int) -> list[int]:
    rows = await _fetchall("SELECT user_id FROM approvals WHERE chat_id = ?", (chat_id,))
    return [r["user_id"] for r in rows]


# ---------------------------------------------------------------- captcha
async def add_captcha(chat_id: int, user_id: int, until: int, answer: str = "") -> None:
    await _exec(
        "INSERT INTO captchas (chat_id, user_id, until, answer) VALUES (?, ?, ?, ?) "
        "ON CONFLICT(chat_id, user_id) DO UPDATE SET until = excluded.until, answer = excluded.answer",
        (chat_id, user_id, until, answer),
    )


async def del_captcha(chat_id: int, user_id: int) -> None:
    await _exec("DELETE FROM captchas WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))


async def expired_captchas(now: int | None = None) -> list[dict]:
    now = now or int(time.time())
    rows = await _fetchall(
        "SELECT * FROM captchas WHERE until > 0 AND until <= ?", (now,)
    )
    return [dict(r) for r in rows]


async def all_captchas() -> list[dict]:
    return [dict(r) for r in await _fetchall("SELECT * FROM captchas")]


# ---------------------------------------------------------------- federations
async def create_fed(fed_id: str, name: str, owner_id: int) -> None:
    await _exec(
        "INSERT INTO feds (fed_id, name, owner_id, created) VALUES (?, ?, ?, ?)",
        (fed_id, name, owner_id, int(time.time())),
    )


async def get_fed(fed_id: str) -> dict | None:
    row = await _fetchone("SELECT * FROM feds WHERE fed_id = ?", (fed_id,))
    return dict(row) if row else None


async def fed_by_name(name: str) -> dict | None:
    row = await _fetchone("SELECT * FROM feds WHERE lower(name) = lower(?)", (name,))
    return dict(row) if row else None


async def join_fed(chat_id: int, fed_id: str) -> None:
    await _exec(
        "INSERT INTO fed_chats (chat_id, fed_id, joined) VALUES (?, ?, ?) "
        "ON CONFLICT(chat_id) DO UPDATE SET fed_id = excluded.fed_id, joined = excluded.joined",
        (chat_id, fed_id, int(time.time())),
    )


async def leave_fed(chat_id: int) -> None:
    await _exec("DELETE FROM fed_chats WHERE chat_id = ?", (chat_id,))


async def chat_fed(chat_id: int) -> dict | None:
    row = await _fetchone(
        "SELECT f.* FROM fed_chats fc JOIN feds f ON f.fed_id = fc.fed_id WHERE fc.chat_id = ?",
        (chat_id,),
    )
    return dict(row) if row else None


async def fed_chats_list(fed_id: str) -> list[int]:
    rows = await _fetchall("SELECT chat_id FROM fed_chats WHERE fed_id = ?", (fed_id,))
    return [r["chat_id"] for r in rows]


async def fed_ban(fed_id: str, user_id: int, reason: str, by_id: int) -> None:
    await _exec(
        "INSERT INTO fed_bans (fed_id, user_id, reason, by_id, at) VALUES (?, ?, ?, ?, ?) "
        "ON CONFLICT(fed_id, user_id) DO UPDATE SET reason = excluded.reason",
        (fed_id, user_id, reason, by_id, int(time.time())),
    )


async def fed_unban(fed_id: str, user_id: int) -> None:
    await _exec("DELETE FROM fed_bans WHERE fed_id = ? AND user_id = ?", (fed_id, user_id))


async def is_fed_banned(fed_id: str, user_id: int) -> bool:
    row = await _fetchone(
        "SELECT 1 FROM fed_bans WHERE fed_id = ? AND user_id = ?", (fed_id, user_id)
    )
    return row is not None


async def fed_ban_list(fed_id: str) -> list[dict]:
    rows = await _fetchall("SELECT * FROM fed_bans WHERE fed_id = ? ORDER BY at DESC", (fed_id,))
    return [dict(r) for r in rows]


async def fed_user_bans(user_id: int) -> list[dict]:
    rows = await _fetchall("SELECT * FROM fed_bans WHERE user_id = ?", (user_id,))
    return [dict(r) for r in rows]
