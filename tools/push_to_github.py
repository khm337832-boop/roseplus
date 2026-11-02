"""tools/push_to_github.py — ဒီ project ထဲက ဖိုင်အားလုံးကို GitHub repo ဆီ တင်တယ်။

သုံးပုံ:
    python tools/push_to_github.py --repo <username>/roseplus --token <TOKEN>
    python tools/push_to_github.py --repo <username>/roseplus --token <TOKEN> --dry-run

လိုအပ်တဲ့ token permission (fine-grained):
    • Repository access : ဒီ repo တစ်ခုတည်း
    • Permissions       : Contents = Read and write
  (classic token ဆိုရင် `repo` scope)

⚠️ Token ကို ဘယ်သူ့ကိုမှ မပေးပါနဲ့။ တင်ပြီးတာနဲ့ GitHub မှာ ပြန် revoke/delete လုပ်ပါ။
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://api.github.com"

SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "data", "node_modules", ".pytest_cache"}
SKIP_FILES = {".env", ".env.local", ".DS_Store"}
SKIP_SUFFIX = {".pyc", ".db", ".db-wal", ".db-shm", ".zip", ".log"}


def collect_files() -> list[Path]:
    out: list[Path] = []
    for path in sorted(ROOT.rglob("*")):
        rel = path.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if not path.is_file():
            continue
        if path.name in SKIP_FILES or path.suffix in SKIP_SUFFIX:
            continue
        out.append(path)
    return out


def request(method: str, url: str, token: str, payload: dict | None = None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "roseplus-pusher")
    if data:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            body = resp.read().decode() or "{}"
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()[:400]
        raise SystemExit(f"❌ GitHub API error {exc.code}: {detail}\n   → token permission / repo အမည် စစ်ပါ") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"❌ Network error: {exc.reason}") from exc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="username/repository")
    parser.add_argument("--token", required=True, help="GitHub token (repo scope)")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--message", default="RosePlus: bilingual Telegram group management bot")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    owner, _, name = args.repo.partition("/")
    if not owner or not name:
        raise SystemExit("❌ --repo ကို `username/repo` ပုံစံ ပေးပါ")

    files = collect_files()
    total_kb = sum(f.stat().st_size for f in files) / 1024
    print(f"📦 ဖိုင် {len(files)} ခု ({total_kb:.0f} KB) တင်မယ် → {owner}/{name} [{args.branch}]")

    if args.dry_run:
        for f in files:
            print("   ", f.relative_to(ROOT))
        return

    status, repo = request("GET", f"{API}/repos/{owner}/{name}", args.token)
    print(f"✅ repo တွေ့တယ်: {repo['full_name']} (private={repo['private']})")

    # 1) branch ရှိပြီးသားလား စစ် — မရှိရင် bootstrap commit တစ်ခု အရင် လုပ်ရတယ်
    #    (GitHub က repo အလွတ်မှာ git data API (blobs) ကို 409 ပြန်ပေးတယ်)
    parent_sha = None
    try:
        _, ref = request("GET", f"{API}/repos/{owner}/{name}/git/ref/heads/{args.branch}", args.token)
        parent_sha = ref["object"]["sha"]
        print(f"ℹ️ branch ရှိပြီးသား — ဒီ commit ပေါ် ဆက်တင်မယ် ({parent_sha[:7]})")
    except SystemExit:
        print(f"ℹ️ branch အလွတ် — '{args.branch}' ကို အရင် ဖန်တီးမယ်")
        request("PUT", f"{API}/repos/{owner}/{name}/contents/.bootstrap", args.token, {
            "message": "init", "branch": args.branch,
            "content": base64.b64encode(b"roseplus\n").decode(),
        })
        _, ref = request("GET", f"{API}/repos/{owner}/{name}/git/ref/heads/{args.branch}", args.token)
        parent_sha = ref["object"]["sha"]

    # 2) ဖိုင်တိုင်းကို blob အနေနဲ့ တင်
    tree_entries = []
    for index, path in enumerate(files, start=1):
        content = base64.b64encode(path.read_bytes()).decode()
        _, blob = request("POST", f"{API}/repos/{owner}/{name}/git/blobs", args.token,
                          {"content": content, "encoding": "base64"})
        executable = path.name.endswith((".sh", ".command", ".bat"))
        tree_entries.append({
            "path": str(path.relative_to(ROOT)).replace("\\", "/"),
            "mode": "100755" if executable else "100644",
            "type": "blob",
            "sha": blob["sha"],
        })
        print(f"   [{index}/{len(files)}] {tree_entries[-1]['path']}")

    # 3) tree + commit + ref ကို တစ်ခါတည်း update
    _, tree = request("POST", f"{API}/repos/{owner}/{name}/git/trees", args.token,
                      {"tree": tree_entries})
    _, commit = request("POST", f"{API}/repos/{owner}/{name}/git/commits", args.token,
                        {"message": args.message, "tree": tree["sha"], "parents": [parent_sha]})
    request("PATCH", f"{API}/repos/{owner}/{name}/git/refs/heads/{args.branch}", args.token,
            {"sha": commit["sha"], "force": True})

    print()
    print(f"🎉 တင်ပြီးပါပြီ → https://github.com/{owner}/{name}/commit/{commit['sha']}")
    print(f"   repo: https://github.com/{owner}/{name}")
    print()
    print("🔐 မှတ်ချက် — အလုပ်ပြီးရင် token ကို GitHub မှာ revoke/delete လုပ်ပါ")


if __name__ == "__main__":
    sys.exit(main())
