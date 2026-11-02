"""tools/push_to_hf.py — Hugging Face Space (အခမဲ့၊ card မလို) ပေါ် bot ကို တင်တယ်။

သုံးပုံ:
    python tools/push_to_hf.py --repo <username>/roseplus-bot --token hf_xxxxx
    python tools/push_to_hf.py --repo <username>/roseplus-bot --token hf_xxxxx --dry-run

လိုအပ်တာ:  pip install huggingface_hub
Token:      huggingface.co/settings/tokens → "Write" permission
"""
from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "data", "node_modules", ".pytest_cache"}
SKIP_FILES = {".env", ".env.local", ".DS_Store"}
SKIP_SUFFIX = {".pyc", ".db", ".db-wal", ".db-shm", ".zip", ".log"}

HF_README = """---
title: RosePlus Bot
emoji: 🌸
colorFrom: purple
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
---

# RosePlus Bot

မြန်မာ/English နှစ်ဘာသာ Telegram group management bot.

**လိုအပ်တဲ့ Secrets (Settings → Variables and secrets):**
- `BOT_TOKEN` — Telegram @BotFather က token
- `DATABASE_URL` — Postgres (Neon/Supabase) connection string
- `DEFAULT_LANG` — `my` သို့ `en` (optional)
"""


def should_copy(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    if any(part in SKIP_DIRS for part in rel.parts):
        return False
    return path.name not in SKIP_FILES and path.suffix not in SKIP_SUFFIX


def build_staging() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="roseplus-hf-"))
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or not should_copy(path):
            continue
        target = tmp / path.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
    # Hugging Face က README.md ရဲ့ အပေါ်ဆုံးမှာ YAML front matter လိုတယ်
    (tmp / "README.md").write_text(HF_README, encoding="utf-8")
    return tmp


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="username/space-name")
    parser.add_argument("--token", required=True, help="hf_...")
    parser.add_argument("--private", action="store_true", help="Space ကို private ထား")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    staging = build_staging()
    files = [p for p in staging.rglob("*") if p.is_file()]
    print(f"📦 ဖိုင် {len(files)} ခု → Hugging Face Space `{args.repo}` (port 7860)")

    if args.dry_run:
        for f in files[:50]:
            print("   ", f.relative_to(staging))
        shutil.rmtree(staging, ignore_errors=True)
        return

    try:
        from huggingface_hub import HfApi
    except ImportError:
        raise SystemExit("❌ `pip install huggingface_hub` ကို အရင် run ပါ")

    api = HfApi(token=args.token)
    try:
        who = api.whoami()
        print(f"✅ ဝင်ပြီး: {who.get('name')}")
    except Exception as exc:
        raise SystemExit(f"❌ token မမှန်ပါ ({exc})")

    url = api.create_repo(
        repo_id=args.repo,
        repo_type="space",
        space_sdk="docker",
        private=args.private,
        exist_ok=True,
    )
    print(f"✅ Space ရှိ/ဖန်တီးပြီး: {url}")

    api.upload_folder(
        folder_path=str(staging),
        repo_id=args.repo,
        repo_type="space",
        commit_message="RosePlus: deploy bot",
    )
    print("✅ ဖိုင်အားလုံး တင်ပြီး")
    shutil.rmtree(staging, ignore_errors=True)

    print()
    print("👉 နောက်အဆင့် (Hugging Face website မှာ):")
    print(f"   1) {url}/settings → Variables and secrets")
    print("      • BOT_TOKEN    = သင့် Telegram bot token  (Secret)")
    print("      • DATABASE_URL = postgresql://...        (Secret)")
    print("      • DEFAULT_LANG = my                      (Variable)")
    print("   2) Space က အလိုအလျောက် ပြန် build ဖြစ်မယ် (2-4 မိနစ်)")
    print("   3) App tab မှာ 'RosePlus is alive' ပေါ်ရမယ်")
    print()
    print("🔐 အလုပ်ပြီးရင် HF token ကို ဖျက်ပါ")


if __name__ == "__main__":
    sys.exit(main())
