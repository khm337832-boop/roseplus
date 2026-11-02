"""tools/push_to_gitlab.py — ဒီ project ထဲက ဖိုင်အားလုံးကို GitLab repo ဆီ တင်တယ်။

သုံးပုံ:
    python tools/push_to_gitlab.py --project <username>/roseplus --token <glpat-...>
    python tools/push_to_gitlab.py --project <username>/roseplus --token <glpat-...> --dry-run

လိုအပ်တဲ့ token scope:  api  (သို့)  write_repository
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://gitlab.com/api/v4"

SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", "data", "node_modules", ".pytest_cache"}
SKIP_FILES = {".env", ".env.local", ".DS_Store"}
SKIP_SUFFIX = {".pyc", ".db", ".db-wal", ".db-shm", ".zip", ".log"}


def collect_files() -> list[Path]:
    out = []
    for path in sorted(ROOT.rglob("*")):
        rel = path.relative_to(ROOT)
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if path.is_file() and path.name not in SKIP_FILES and path.suffix not in SKIP_SUFFIX:
            out.append(path)
    return out


def request(method: str, url: str, token: str, payload: dict | None = None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("PRIVATE-TOKEN", token)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode() or "{}"
            return resp.status, json.loads(body)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode()[:500]
        raise SystemExit(f"❌ GitLab API error {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"❌ Network error: {exc.reason}") from exc


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", required=True, help="username/roseplus")
    parser.add_argument("--token", required=True, help="glpat-...")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--message", default="RosePlus: bilingual Telegram group management bot")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    files = collect_files()
    total_kb = sum(f.stat().st_size for f in files) / 1024
    print(f"📦 ဖိုင် {len(files)} ခု ({total_kb:.0f} KB) တင်မယ် → {args.project} [{args.branch}]")
    if args.dry_run:
        for f in files:
            print("   ", f.relative_to(ROOT))
        return

    project_id = urllib.parse.quote(args.project, safe="")
    status, project = request("GET", f"{API}/projects/{project_id}", args.token)
    print(f"✅ project တွေ့တယ်: {project['path_with_namespace']} "
          f"(visibility={project.get('visibility')})")

    # ရှိပြီးသား ဖိုင်တွေကို သိ (create / update ကို ခွဲဖို့)
    existing: set[str] = set()
    try:
        _, tree = request(
            "GET",
            f"{API}/projects/{project_id}/repository/tree?recursive=true&per_page=100",
            args.token,
        )
        if isinstance(tree, list):
            existing = {item["path"] for item in tree if item["type"] == "blob"}
    except SystemExit:
        existing = set()

    actions = []
    for path in files:
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        actions.append({
            "action": "update" if rel in existing else "create",
            "file_path": rel,
            "content": path.read_text(encoding="utf-8", errors="replace")
            if _is_text(path) else "",
        })

    # ဖိုင်အများကြီး တစ်ခါတည်း (GitLab က 100 ခုအထိ ရ)
    for start in range(0, len(actions), 50):
        chunk = actions[start:start + 50]
        _, commit = request("POST", f"{API}/projects/{project_id}/repository/commits", args.token, {
            "branch": args.branch,
            "commit_message": args.message,
            "actions": chunk,
        })
        print(f"   ✅ {len(chunk)} ဖိုင် တင်ပြီး → commit {commit.get('short_id')}")

    print()
    print(f"🎉 တင်ပြီးပါပြီ → {project['web_url']}")
    print(f"   Render မှာ သုံးရန် URL: {project['http_url_to_repo']}")
    print()
    print("🔐 အလုပ်ပြီးရင် token ကို GitLab မှာ revoke လုပ်ပါ")


def _is_text(path: Path) -> bool:
    try:
        path.read_text(encoding="utf-8")
        return True
    except UnicodeDecodeError:
        return False


if __name__ == "__main__":
    sys.exit(main())
