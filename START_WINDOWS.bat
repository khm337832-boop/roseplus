@echo off
chcp 65001 >nul
title Goii Auto Bot Bot
cd /d "%~dp0"

echo ==================================================
echo    Goii Auto Bot Bot  -  Automatic Setup ^& Start
echo ==================================================
echo.

where python >nul 2>nul
if errorlevel 1 goto nopython

if exist .venv goto install

echo [1/4] Creating local environment (first time only)...
python -m venv .venv
if errorlevel 1 goto venvfail

:install
echo [2/4] Installing libraries (first time may take 1-2 minutes)...
call ".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
call ".venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
if errorlevel 1 goto pipfail

if exist .env goto run
echo.
echo [3/4] First-time setup - you only do this once
echo.
echo  1) Open Telegram, search @BotFather, send /mybots
echo  2) Choose your bot, tap API Token, copy it
echo.
set /p TOKEN=  Paste your token here, then press Enter: 
echo.
set /p BOTNAME=  Your bot username (without @): 
> .env echo BOT_TOKEN=%TOKEN%
>> .env echo DEFAULT_LANG=my
>> .env echo BOT_USERNAME=%BOTNAME%
>> .env echo DB_PATH=data/roseplus.db
echo.
echo  Saved to .env
echo.

:run
echo [4/4] Starting the bot...
echo.
echo  ------------------------------------------------------------
echo   Keep THIS window open while you use the bot.
echo   To stop the bot: close this window or press Ctrl+C
echo  ------------------------------------------------------------
echo.
".venv\Scripts\python.exe" bot.py
echo.
echo Bot stopped. Press any key to close.
pause >nul
exit /b 0

:nopython
echo [X] Python is not installed.
echo.
echo     Go to:  https://www.python.org/downloads/
echo     Download, run the installer, and IMPORTANT:
echo     tick the box  "Add python.exe to PATH"
echo.
echo     Then double-click this file again.
pause
exit /b 1

:venvfail
echo [X] Could not create the environment. Reinstall Python with "Add to PATH" ticked.
pause
exit /b 1

:pipfail
echo [X] Could not install libraries. Check your internet connection and try again.
pause
exit /b 1
