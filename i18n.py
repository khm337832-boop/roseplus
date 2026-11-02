"""i18n.py — locales/*.json ထဲက ဘာသာစကား ဖိုင်တွေကို ဖတ်ပြီး t() နဲ့ ဘာသာပြန်ပါတယ်။"""
from __future__ import annotations

import json
from pathlib import Path

LANG_DIR = Path(__file__).resolve().parent / "locales"
_cache: dict[str, dict[str, str]] = {}
_fallback = "en"


def load() -> None:
    _cache.clear()
    if not LANG_DIR.is_dir():
        return
    for path in sorted(LANG_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:  # pragma: no cover
            raise SystemExit(f"locale file {path.name} မှာ JSON အမှားရှိတယ်: {exc}")
        _cache[path.stem] = data


def available() -> list[str]:
    return sorted(_cache)


def t(lang: str | None, key: str, **kwargs) -> str:
    """ဘာသာပြန် စာသား ယူခြင်း။ မရှိရင် en → key အစဉ်လိုက် ပြန်ပေးတယ်။"""
    lang = lang or _fallback
    text = _cache.get(lang, {}).get(key)
    if text is None:
        text = _cache.get(_fallback, {}).get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text


def missing_keys() -> dict[str, list[str]]:
    """ဘာသာပြန် လိုနေတဲ့ key တွေ (check script အတွက်)။"""
    if not _cache:
        return {}
    all_keys = set()
    for d in _cache.values():
        all_keys |= set(d)
    out = {}
    for lang, d in _cache.items():
        miss = sorted(all_keys - set(d))
        if miss:
            out[lang] = miss
    return out
