# 🌸 RosePlus — မြန်မာ/English Group Management Bot

**@MissRose_bot ရဲ့ feature တွေကို အခြေခံပြီး ကိုယ်ပိုင် server ပေါ်မှာ အခမဲ့ run နိုင်အောင် ရေးထားတဲ့ Telegram group management bot**

- 🆓 **အခမဲ့** — Telegram Bot API အခမဲ့ + SQLite (database server မလို) + free-tier hosting သုံးနိုင်
- 🇲🇲 **မြန်မာ / 🇬🇧 English** — `/lang my` / `/lang en` နဲ့ ရွေးနိုင်၊ ဘာသာပြန်ချက် အားလုံး `locales/*.json` မှာ ရှိတာမို့ ကိုယ်တိုင် ပြင်နိုင်
- ⚙️ **Button panel** — `/settings` နှိပ်ရုံနဲ့ welcome/captcha/antiflood/antiraid/locks ချိန် (command ကျက်စရာမလို)
- 🛡️ MissRose နဲ့ တူတဲ့ feature တွေ + ပိုကောင်းတဲ့ အချက်တွေ (အောက်မှာ ကြည့်)
- 🔒 Data က ကိုယ့် server ပေါ်မှာပဲ — third-party ဆီ မပေးပို့

---

## ၁။ ဘာ feature တွေ ပါလဲ

### Moderation
| Command | အလုပ် |
|---|---|
| `/ban` `/unban` `/kick` | အပြီးအပိုင် ပိတ် / ပြန်ဖွင့် / ထုတ် |
| `/mute` `/unmute` `/tmute 10m` `/tban 1d` | အချိန်ကန့်သတ် ပါဝင်တယ် |
| `/warn` `/unwarn` `/warns` `/resetwarns` | Warn စနစ် (limit ပြည့်ရင် auto ban/kick/mute) |
| `/setwarnlimit 3` `/setwarnmode ban` | Warn setting |
| `/purge` `/del` `/pin` `/unpin` `/permapin` | Message စီမံ |
| `/report` | Admin တွေကို tag ပြီး အစီရင်ခံ |
| `/approve` `/unapprove` `/approved` | ယုံကြည်ရသူ (lock/flood က ကင်းလွတ်) |
| `/promote` `/demote` `/adminlist` `/admincache` | Admin စီမံ |

### Anti-spam
| Command | အလုပ် |
|---|---|
| `/lock url sticker gif forward media mentions …` | မျိုးအစားအလိုက် ပိတ် (23 မျိုး) |
| `/unlock` `/locks` `/locktypes` | ပြန်ဖွင့် / စာရင်း |
| `/addblocklist စကားလုံး` `/unblocklist` `/blocklist` `/unblocklistall` | စကားလုံး ပိတ် |
| `/blocklistmode delete\|warn\|mute\|tmute 10m\|kick\|ban\|tban 1d` | တွေ့ရင် ဘာလုပ်မလဲ |
| `/setflood 5` `/setfloodtimer 5 10s` `/setfloodmode tmute 10m` `/clearflood on` `/flood` | Antiflood |
| `/captcha on` `/captchamode button\|math` `/captchakick on` `/captchakicktime 10m` `/captcharules on` `/setcaptchatext` | CAPTCHA (နှစ်ဘာသာ၊ math mode ပါ) |
| `/antiraid on` `/raidtime 1h` `/raidlimit 8` | Raid ကာကွယ်ရေး |

### Greetings & content
- `/setwelcome` `/welcome on` `/setgoodbye` `/goodbye on` `/resetwelcome` `/cleanwelcome on` `/cleanservice on`
  - Variable: `{first} {last} {fullname} {username} {mention} {id} {chatname} {count} {rules}`
  - Button: `[စာသား](buttonurl://https://example.com)`
- `/save <နာမည်>` `/get` `/notes` `/clear` + `#နာမည်` ရိုက်ရင် auto ဖြေ
- `/filter <trigger> <reply>` `/filters` `/stop` + `{admin}` `{protect}` tag
- `/setrules` `/rules` `/privaterules on` `/resetrules`

### အခြား
- `/newfed` `/joinfed` `/fban` `/funban` `/fbanlist` — federation (group အများကို ban တစ်ချက်နဲ့)
- `/export` `/import` — setting တွေ JSON နဲ့ backup/ကူး
- `/logchannel @channel` — action တွေ log
- `/disable <cmd>` `/enable` `/disabled` — command ပိတ်/ဖွင့်
- `/settings` button panel · `/lang` · `/id` · `/info` · `/ping` · `/stats`

### MissRose ထက် ပိုကောင်းတဲ့ အချက်တွေ
1. **မြန်မာဘာသာ အပြည့်အစုံ** — message, error, panel အားလုံး မြန်မာလို (MissRose မှာ မြန်မာ မပြည့်စုံ)
2. **မြန်မာစာ blocklist/filter** — myanmar script မှာ word-boundary မရှိတာကို သတိထားပြီး substring matching သုံး
3. **Button settings panel** — command မကျက်ဘဲ နှိပ်ရုံ
4. **ကိုယ့် data ကိုယ်ပိုင်** — SQLite file က သင့် server ပေါ်မှာ
5. **AI/extension ထည့်ရလွယ်** — plugin file တစ်ခု ထပ်ရေးရုံ
6. **Export/Import + `tools/` မှာ self-test** — deploy မလုပ်ခင် စမ်းလို့ရ

---

## ၂။ ၅ မိနစ်အတွင်း စတင်ခြင်း

### အဆင့် ၁ — BotFather မှာ bot ဖန်တီး
1. Telegram မှာ **@BotFather** ကို ဖွင့်ပါ → `/newbot`
2. အမည် ပေးပါ (ဥပမာ `My Group Guard`) → username ပေးပါ (ဥပမာ `mygroup_guard_bot`)
3. ရလာတဲ့ **token** ကို copy လုပ်ပါ (`123456789:AAH…`)

### အဆင့် ၂ — Privacy mode ပိတ် (အရေးအကြီးဆုံး ⚠️)
BotFather မှာ `/setprivacy` → သင့် bot ရွေး → **Disable**

> မပိတ်ရင် bot က `/command` နဲ့ reply တွေပဲ မြင်မယ်။ **locks, blocklist, filters** တွေ အလုပ်မလုပ်ပါ။

### အဆင့် ၃ — Group ထဲ ထည့်ပြီး Admin ပေး
Group → Administrators → Add Administrator → သင့် bot ရွေး → **right အားလုံး ပေး**

### အဆင့် ၄ — Token စစ်ပြီး Run လုပ်ပါ
```bash
cd roseplus
cp .env.example .env        # BOT_TOKEN=... ထည့်ပါ
python tools/setup_check.py # token + privacy mode + DB အားလုံး စစ်ပေးတယ်
./run.sh                    # venv ဖန်တီးပြီး run မယ်
```
ဒါမှမဟုတ် —
```bash
pip install -r requirements.txt
python bot.py
```
Terminal မှာ `🤖 RosePlus started as @yourbot` ပေါ်ရင် အောင်မြင်ပါပြီ။

### အဆင့် ၅ — Group ထဲမှာ စမ်းပါ
```
/settings                 → button panel
/setwelcome မင်္ဂလာပါ {mention}၊ {chatname} ကို ကြိုဆိုပါတယ် 🌸
/captcha on
/setflood 5
/setfloodmode tmute 10m
/lock url forward
/addblocklist ငွေလဲ
/setrules ၁။ ယဉ်ကျေးပါ ၂။ Spam မလုပ်ပါ
```

---

## ၃။ အခမဲ့ Hosting ရွေးချယ်စရာများ

| နည်းလမ်း | ကုန်ကျစရိတ် | အားသာချက် | အားနည်းချက် |
|---|---|---|---|
| **ကိုယ့် PC / ဖုန်း (Termux)** | ၀ | အလွယ်ဆုံး၊ setup မလို | PC ဖွင့်ထားမှ အလုပ်လုပ် |
| **Oracle Cloud Always Free** ⭐ | ၀ (card verify လို) | ၂၄/၇ တကယ် အခမဲ့ VPS (Arm 2 OCPU / 12GB) | Linux နည်းနည်း ရမယ်၊ idle VM ပြန်သိမ်းနိုင် |
| **Render free tier** ⭐ | ၀ | GitHub ကနေ Docker နဲ့ အလွယ်တင် | ၁၅ မိနစ် idle ဆို sleep (ping လို) + disk မရှိ (Postgres လို) → **§၇** |
| **Koyeb free** | ၀ (card) | sleep နည်း | resource ကန့်သတ် (512MB) |
| **Railway** | trial credit | အလွယ်ဆုံး | အချိန်ကန့်သတ် |

### Oracle Cloud (အကြံပြုချက် — တကယ် ၂၄/၇ အခမဲ့)
```bash
# 1) Ubuntu VM တစ်ခု ဖန်တီး (Always Free eligible shape)
# 2) SSH ဝင်ပြီး
sudo apt update && sudo apt install -y python3 python3-venv git
git clone <သင့် repo> roseplus && cd roseplus
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
cp .env.example .env && nano .env       # BOT_TOKEN ထည့်
# 3) systemd service (crash ဖြစ်ရင် auto ပြန် run)
sudo tee /etc/systemd/system/roseplus.service >/dev/null <<'EOF'
[Unit]
Description=RosePlus Telegram Bot
After=network.target

[Service]
WorkingDirectory=/home/ubuntu/roseplus
ExecStart=/home/ubuntu/roseplus/.venv/bin/python bot.py
Restart=always
RestartSec=5
User=ubuntu

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl enable --now roseplus
sudo journalctl -u roseplus -f        # log ကြည့်
```

### Docker (ဘယ် VPS မဆို)
```bash
cp .env.example .env && nano .env
docker compose up -d --build
docker compose logs -f
```

> 💾 **Backup**: `data/roseplus.db` ကို ကော်ပီထားရုံနဲ့ setting + warns + notes အားလုံး ပါတယ်။ `/export` နဲ့လည်း ထုတ်နိုင်တယ်။

---

## ၄။ Code ဖွဲ့စည်းပုံ

```
roseplus/
├── bot.py              # entry point, router/middleware ချိတ်ဆက်မှု
├── config.py           # .env configuration
├── db.py               # SQLite schema + အားလုံး query
├── i18n.py             # ဘာသာပြန် loader
├── helpers.py          # permission, time parse, lock detect, button parse
├── common.py           # chat_lang, log_action
├── locales/
│   ├── my.json         # မြန်မာ (ဒီဖိုင်ပဲ ပြင်ရင် စာသား ပြောင်းတယ်)
│   └── en.json
├── plugins/
│   ├── core.py         # /start /help /lang /id /info /stats /export /import /disable
│   ├── moderation.py   # ban/kick/mute/warn/purge/pin/report/approve/promote
│   ├── antispam.py     # locks, blocklist, antiflood, antiraid
│   ├── captcha.py      # CAPTCHA + အချိန်ကုန် job
│   ├── greetings.py    # welcome/goodbye + member join flow
│   ├── content.py      # notes, filters, rules
│   ├── federation.py   # federation
│   ├── settings.py     # /settings button panel
│   └── watcher.py      # message တိုင်း ဖြတ်စစ်တဲ့ engine
├── render.yaml         # Render Blueprint (တစ်ချက်နှိပ်တင်)
└── tools/
    ├── setup_check.py  # token / privacy mode / DB စစ်ဆေးခြင်း (run ခင် အရင် run ပါ)
    ├── db_check.py     # SQLite/Postgres အားလုံး အလုပ်လုပ်မလုပ်
    ├── pg_syntax_check.py  # SQL တွေ Postgres နဲ့ ကိုက်ညီမလား (pglast)
    ├── selfcheck.py    # DB + helper test (token မလို)
    └── dryrun.py       # Telegram မချိတ်ဘဲ handler တွေ စမ်း
```

### စမ်းသပ်ခြင်း
```bash
python tools/setup_check.py  # token အလုပ်လုပ်လား, privacy mode ပိတ်ထားလား, DB ရေးနိုင်လား
python tools/db_check.py     # SQLite သို့ Postgres (DATABASE_URL) ကို အပြည့် စမ်း
python tools/selfcheck.py    # locale key, DB, antiflood, lock detection
python tools/dryrun.py       # /help /ban /lock /filter /settings /captcha … တွေ အလုပ်လုပ်မလုပ်
```

### စာသား ပြင်ချင်ရင်
`locales/my.json` ထဲက value ကို ပြင်ရုံ။ Key အသစ် ထည့်ရင် `en.json` မှာပါ ထည့်ပါ (မဟုတ်ရင် `selfcheck.py` က သတိပေးမယ်)။

### Command အသစ် ထည့်ချင်ရင်
```python
# plugins/content.py ထဲ ထပ်ရေးရုံ
@router.message(Command("hello"))
async def cmd_hello(message: Message) -> None:
    lang = await lang_of(message)
    await message.reply("👋 " + i18n.t(lang, "lang_set"))
```

---

## ၅။ သတိထားရမယ့် အချက်များ

1. **Privacy mode ပိတ်ဖို့ မမေ့ပါ** — မဟုတ်ရင် locks/blocklist/filters အလုပ်မလုပ်
2. **Admin right** — ban/mute/delete/pin တွေအတွက် bot ကို admin ပေးရမယ်
3. **Telegram rate limit** — ~30 msg/ကမ္ဘာလုံး/စက္ကန့်၊ chat တစ်ခုကို ~20/မိနစ် (အလွန်အကျွံ ပို့ရင် `retry_after` တွေ့နိုင်)
4. **SQLite** — group ၁၀၀၀၀ ကျော် ဖြစ်လာရင် PostgreSQL ကို ပြောင်းတာ ပိုကောင်း (db.py ကို ပြင်ရုံ)
5. **Token ကို ဘယ်သူ့ကိုမှ မပေးပါ** — `.env` ကို git မတင်ပါ (`.gitignore` မှာ ပါပြီးသား)

---

## ၆။ နောက် ထပ်လုပ်နိုင်တဲ့ အဆင့်များ (ပြောရင် ဆက်လုပ်ပေးမယ်)

- 🤖 AI moderation — spam ကို keyword မဟုတ်ဘဲ AI နဲ့ ခွဲခြား (OpenAI/Gemini API key ထည့်ရုံ)
- 📊 Web dashboard — group stats, warn list ကို browser မှာ ကြည့်
- 🌐 Join-request CAPTCHA (approval portal) — MissRose ရဲ့ အင်အားအရှိဆုံး feature
- 🔁 PostgreSQL migration + multi-instance
- 📝 Scheduled messages / auto-post
- 🌍 ဘာသာစကား ထပ်ထည့် (Shan, Karen, Thai…)

---

## ၇။ GitHub + Render မှာ တင်ခြင်း (အဆင့်ဆင့်)

### ၇.၁ Code ကို GitHub တင်
```bash
cd roseplus
git init
git add .
git commit -m "RosePlus: bilingual Telegram group management bot"
git branch -M main
git remote add origin https://github.com/<username>/roseplus.git
git push -u origin main
```
⚠️ **`.env` ကို မတင်မိပါစေနဲ့** (token ပါတယ်)။ `.gitignore` မှာ ပါပြီးသားပါ — `git status` နဲ့ စစ်ပါ။

### ၇.၂ Render မှာ Service ဖန်တီး
နည်း (က) — **Blueprint (အလွယ်ဆုံး)**
1. [render.com](https://render.com) → **New +** → **Blueprint**
2. သင့် GitHub repo ရွေး → `render.yaml` ကို Render က အလိုအလျောက် ဖတ်မယ်
3. `BOT_TOKEN`, `BOT_USERNAME`, `DATABASE_URL` တွေ ဖြည့်ပြီး **Apply**

နည်း (ခ) — **Manual**
1. **New +** → **Web Service** → repo ချိတ်
2. Runtime: **Docker** (repo ထဲက `Dockerfile`) 
   *သို့မဟုတ်* Runtime **Python** → Build: `pip install -r requirements.txt` → Start: `python bot.py`
3. Instance Type: **Free** → Environment မှာ `BOT_TOKEN`, `DEFAULT_LANG=my`, `BOT_USERNAME` ထည့်
4. **Create Web Service**

> Render free က **HTTP port** လိုတယ်။ `bot.py` က `PORT` env ရှိရင် `0.0.0.0:$PORT` မှာ HTTP server ဖွင့်ပြီး
> `RosePlus is alive` ပြန်ပေးတယ်။ Bot က polling နဲ့ ဆက်အလုပ်လုပ်နေမယ် — webhook မလိုပါ။
> Deploy ပြီး `https://<app>.onrender.com` ဖွင့်ကြည့်ရင် အဲ့စာသား ပေါ်ရမယ်။

### ၇.၃ ⚠️ Data မပျောက်အောင် Postgres သုံး (Render free မှာ disk မရှိ)
Render free မှာ file system က **restart/redeploy တိုင်း ပြန်လည်သတ်မှတ်** ခံရတာမို့ SQLite file ပျက်မယ်။
အခမဲ့ Postgres တစ်ခု ယူပါ —

| ဝန်ဆောင်မှု | Free | လုပ်ရမှာ |
|---|---|---|
| **Supabase** | 500MB, သက်တမ်းမကုန် | New Project → Settings → Database → **Connection string (URI)** copy |
| **Neon** | 0.5GB | Create project → **Connection string** copy |

ပြီးရင် Render → Environment → **`DATABASE_URL`** = `postgresql://...` ထည့်ပါ။
Bot က `DATABASE_URL` ရှိရင် Postgres ကို အလိုအလျောက် သုံးမယ် (မရှိရင် SQLite)။

**Deploy မလုပ်ခင် ကိုယ့်ကွန်ပျူတာကနေ အရင် စစ်နိုင်တယ်:**
```bash
DATABASE_URL="postgresql://..." python tools/db_check.py
```
(ဒီ script က table ဖန်တီးပြီး function အားလုံး တကယ် စမ်းတယ် — ✅ အားလုံး ရရင် Render မှာလည်း အလုပ်လုပ်မယ်)

> SQL အားလုံး Postgres နဲ့ ကိုက်ညီမလား ဒီမှာ စစ်ထားပြီးပါပြီ — `python tools/pg_syntax_check.py` (pglast လိုတယ်)
> → 48 statement လုံး PostgreSQL grammar အတိုင်း မှန်ကန်တယ်။

### ၇.၄ Free tier က အိပ်မသွားအောင် (အရေးကြီး)
Render free က **၁၅ မိနစ် request မဝင်ရင် အိပ်တယ်** → bot က ခေတ္တ ရပ်မယ်။
1. [UptimeRobot](https://uptimerobot.com) (အခမဲ့) → **Add New Monitor** → HTTP(s)
2. URL = `https://<app>.onrender.com` → Interval = **5 minutes**
3. ဒါဆို ၂၄/၇ နိုးနေမယ် (Render free က **750 နာရီ/လ** ကန့်သတ်ချက် ရှိတာမို့ service တစ်ခုပဲ ထားပါ)

### ၇.၅ စစ်ဆေးခြင်း
- Render → **Logs** မှာ `🤖 RosePlus started as @your_bot` ပေါ်လား
- `https://<app>.onrender.com` → `RosePlus is alive`
- Telegram → bot ကို group admin ပေး → `/settings` ရိုက်

### ၇.၆ Update တင်ချင်ရင်
```bash
git add . && git commit -m "update" && git push
```
Render က အလိုအလျောက် ပြန် deploy လုပ်မယ် (`autoDeploy: true`)。

---

## ၈။ English quickstart

```bash
cp .env.example .env      # put your BotFather token in BOT_TOKEN
pip install -r requirements.txt
python bot.py
```
1. Create a bot with **@BotFather** → `/newbot`
2. **Disable privacy mode**: `/setprivacy` → your bot → Disable
3. Add the bot to your group and grant **all admin rights**
4. Run it, then send `/settings` in the group

Features: moderation (ban/kick/mute/warn/purge/pin/report), anti-spam (locks, blocklist,
antiflood, CAPTCHA button/math, anti-raid), greetings, notes, filters, rules,
federations, log channels, export/import — all bilingual (Myanmar/English) and free to self-host.

---

Made with 🌸 — data stays on your server, no third-party service required.
