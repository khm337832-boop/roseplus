"""tools/pg_syntax_check.py — Postgres နဲ့ ကိုက်ညီမလား စစ်ဆေးတယ် (dev tool)

ဒီ script က bot ရဲ့ SQL အားလုံးကို SQLite ပေါ်မှာ တကယ် run ပြီး ဖမ်းယူကာ
PostgreSQL grammar (pglast) နဲ့ ပြန်စစ်တယ်။ Server တစ်ခု မလိုပါ။

run:  pip install pglast  &&  python tools/pg_syntax_check.py
"""
from __future__ import annotations

import asyncio
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "tools"))

SQLS: list[str] = []
FAILS: list[str] = []


async def main() -> None:
    try:
        from pglast import parse_sql
    except ImportError:
        print("⚠️  pglast မရှိပါ — `pip install pglast` ရိုက်ပြီး ထပ်စမ်းပါ")
        raise SystemExit(2)

    import db
    import db_check

    await db.init(os.path.join(tempfile.mkdtemp(), "pgsyntax.db"))
    backend = db._backend

    # --- backend method တွေကို wrap လုပ်ပြီး SQL ဖမ်းမယ် ---
    orig_fetchone, orig_fetchall, orig_execute = (
        backend.fetchone, backend.fetchall, backend.execute,
    )

    async def wrap(orig, sql, params):
        SQLS.append(sql)
        return await orig(sql, params)

    backend.fetchone = lambda sql, params: wrap(orig_fetchone, sql, params)
    backend.fetchall = lambda sql, params: wrap(orig_fetchall, sql, params)
    backend.execute = lambda sql, params: wrap(orig_execute, sql, params)

    # --- schema (CREATE TABLE …) ကိုပါ စစ်ဖို့ ---
    SQLS.extend([s.strip() for s in db.SCHEMA.split(";") if s.strip()])

    print("1) db function အားလုံးကို run ပြီး SQL ဖမ်းယူခြင်း")
    await db_check.exercise()
    await db.close()
    print(f"   SQL statement {len(SQLS)} ခု ဖမ်းမိပြီး")

    print("\n2) PostgreSQL grammar နဲ့ စစ်ဆေးခြင်း")
    translate = db._PostgresBackend._sql
    seen = set()
    for sql in SQLS:
        pg_sql = translate(sql)
        if pg_sql in seen:
            continue
        seen.add(pg_sql)
        try:
            parse_sql(pg_sql)
        except Exception as exc:  # pglast ParseError
            FAILS.append(pg_sql)
            print(f"  ❌ {pg_sql[:110]}\n     → {str(exc)[:160]}")

    print(f"\n3) ရလဒ် — စစ်ပြီး {len(seen)} ခု / မအောင်မြင် {len(FAILS)} ခု")

    print("\n4) SQLite-only syntax မကျန်အောင် စစ်ခြင်း")
    joined = " ".join(SQLS).upper()
    for bad, hint in (
        ("INSERT OR IGNORE", "→ `INSERT … ON CONFLICT DO NOTHING` သုံးပါ"),
        ("AUTOINCREMENT", "→ BIGINT PRIMARY KEY သုံးပါ"),
        ("PRAGMA", "→ PRAGMA ကို backend ထဲမှာပဲ ထားပါ"),
        ("IFNULL(", "→ COALESCE() သုံးပါ"),
    ):
        if bad in joined:
            FAILS.append(bad)
            print(f"  ❌ {bad} တွေ့တယ် {hint}")
        else:
            print(f"  ✅ {bad} မရှိပါ")

    if FAILS:
        print("\n❌ Postgres နဲ့ မကိုက်ညီတာ ရှိတယ်")
        raise SystemExit(1)
    print("\n🎉 SQL အားလုံး Postgres နဲ့ ကိုက်ညီပါတယ်")


if __name__ == "__main__":
    asyncio.run(main())
