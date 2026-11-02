#!/usr/bin/env bash
# အလွယ်တကူ run ဖို့:  ./run.sh
set -e
cd "$(dirname "$0")"
if [ ! -f .env ]; then
  echo "❌ .env မရှိပါ — .env.example ကို .env အဖြစ် copy ပြီး BOT_TOKEN ထည့်ပါ"
  exit 1
fi
if [ ! -d .venv ]; then
  echo "📦 venv ဖန်တီးနေတယ်…"
  python3 -m venv .venv
  ./.venv/bin/pip install -q -r requirements.txt
fi
exec ./.venv/bin/python bot.py
