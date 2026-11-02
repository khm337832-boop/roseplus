#!/bin/bash
cd "$(dirname "$0")" || exit 1
echo "=================================================="
echo "   Goii Auto Bot Bot  -  Automatic Setup & Start"
echo "=================================================="
echo

if ! command -v python3 >/dev/null 2>&1; then
  echo "[X] Python 3 is not installed."
  echo "    Install it from: https://www.python.org/downloads/"
  echo "    Then double-click this file again."
  read -r -p "Press Enter to close..."
  exit 1
fi

if [ ! -d .venv ]; then
  echo "[1/4] Creating local environment (first time only)..."
  python3 -m venv .venv || { echo "[X] venv failed"; read -r; exit 1; }
fi

echo "[2/4] Installing libraries (first time may take 1-2 minutes)..."
./.venv/bin/python -m pip install --quiet --upgrade pip
./.venv/bin/python -m pip install --quiet -r requirements.txt || { echo "[X] pip failed - check internet"; read -r; exit 1; }

if [ ! -f .env ]; then
  echo
  echo "[3/4] First-time setup - you only do this once"
  echo "  1) Open Telegram, search @BotFather, send /mybots"
  echo "  2) Choose your bot, tap API Token, copy it"
  echo
  read -r -p "  Paste your token here, then press Enter: " TOKEN
  read -r -p "  Your bot username (without @): " BOTNAME
  {
    echo "BOT_TOKEN=$TOKEN"
    echo "DEFAULT_LANG=my"
    echo "BOT_USERNAME=$BOTNAME"
    echo "DB_PATH=data/roseplus.db"
  } > .env
  echo "  Saved to .env"
  echo
fi

echo "[4/4] Starting the bot..."
echo
echo "  ------------------------------------------------------------"
echo "   Keep THIS window open while you use the bot."
echo "   To stop the bot: press Ctrl+C or close this window."
echo "  ------------------------------------------------------------"
echo
./.venv/bin/python bot.py
echo
read -r -p "Bot stopped. Press Enter to close..."
