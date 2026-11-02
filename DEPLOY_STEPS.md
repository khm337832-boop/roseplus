# 🪜 Goii Auto Bot တင်ခြင်း — တစ်ဆင့်ချင်း လမ်းညွှန်

> **ဘယ်လို သုံးမလဲ** — အဆင့်တစ်ခုကို အပြီးလုပ်ပြီး "✅ စစ်ဆေးချက်" ကို ဖတ်ပါ။ အဲ့မှာ ပြောထားတာ တွေ့ရင် နောက်တစ်ဆင့် တက်ပါ။
> မတွေ့ရင် အဲ့အဆင့်ရဲ့ "⚠️ မအောင်ရင်" ကို ကြည့်ပါ။ အားလုံး အတူတူ ၄၅ မိနစ် – ၁ နာရီ လောက် ကြာနိုင်ပါတယ်။ တစ်ခါတည်း အကုန်လုပ်ဖို့ မလိုပါ — ရပ်ပြီး နောက်မှ ဆက်လို့ရပါတယ်။

**သင်လုပ်မယ့် အစီအစဉ် (အကြမ်းဖျင်း)**

```
ကွန်ပျူတာပေါ် စမ်း  →  GitHub တင်  →  အခမဲ့ Postgres  →  Render တင်  →  အိပ်မသွားအောင် ping  →  group မှာ ချိန်
 (၁၅ မိနစ်)          (၁၀ မိနစ်)      (၅ မိနစ်)        (၁၀ မိနစ်)      (၅ မိနစ်)            (၁၀ မိနစ်)
```

---

# အပိုင်း ၁ — ကွန်ပျူတာပေါ်မှာ အရင် စမ်းခြင်း

## အဆင့် ၁ — Code ကို ကွန်ပျူတာပေါ် ယူ

1. ဒီ chat ရဲ့ workspace ထဲက **`roseplus.zip`** ကို ဒေါင်းလုဒ် လုပ်ပါ
2. ဖိြဖြေ (Extract) ပါ → `roseplus` folder တစ်ခု ရလာမယ်

**ဥပမာ နေရာ** — `Desktop\roseplus` (Windows) / `~/Desktop/roseplus` (Mac)

✅ **စစ်ဆေးချက်** — folder ထဲမှာ `bot.py`, `requirements.txt`, `locales` folder တွေ တွေ့ရမယ်

---

## အဆင့် ၂ — Python ရှိ/မရှိ စစ်

**Windows** — Start → **PowerShell** ဖွင့်ပြီး:
```powershell
python --version
```
**Mac / Linux** — Terminal ဖွင့်ပြီး:
```bash
python3 --version
```

✅ **စစ်ဆေးချက်** — `Python 3.11.x` / `3.12.x` / `3.13.x` လို ပေါ်ရမယ်

⚠️ **မအောင်ရင်**
- `'python' is not recognized` ဆိုရင် → [python.org/downloads](https://python.org/downloads) ကနေ install လုပ်ပါ
- Windows မှာ install လုပ်တဲ့အခါ **"Add Python to PATH"** ✅ အမှတ်ခြစ်ဖို့ မမေ့ပါ
- Mac: `python3` ကို သုံးပါ (`python` မဟုတ်)

---

## အဆင့် ၃ — `.env` ဖိုင် ဖန်တီးပြီး token ထည့်

**Windows** (PowerShell — `roseplus` folder ထဲ ဝင်ရောက်ပြီး):
```powershell
cd Desktop\roseplus
copy .env.example .env
notepad .env
```
**Mac / Linux**:
```bash
cd ~/Desktop/roseplus
cp .env.example .env
nano .env          # (သို့) open -e .env
```

`.env` ထဲမှာ ဒီလို ဖြစ်အောင် ပြင်ပါ:
```
BOT_TOKEN=123456789:AAH...သင့် token...
DEFAULT_LANG=my
BOT_USERNAME=သင့်_bot_username
DB_PATH=data/roseplus.db
```
> `BOT_USERNAME` မှာ **@ မပါ** ရပါ (ဥပမာ `mygroup_guard_bot`)

သိမ်းပြီး ပိတ်ပါ (nano ဆိုရင် `Ctrl+O` → Enter → `Ctrl+X`)

✅ **စစ်ဆေးချက်** — `roseplus` folder ထဲမှာ `.env` ဖိုင် ရှိနေပြီ

⚠️ **သတိ** — `.env` ကို **ဘယ်တော့မှ** GitHub မတင်ပါနဲ့၊ ဘယ်သူ့ကိုမှ မပို့ပါနဲ့။ အဲ့ထဲမှာ သင့် bot ရဲ့ သော့ ပါတယ်။

---

## အဆင့် ၄ — Library တွေ install + စစ်ဆေး

```bash
pip install -r requirements.txt
python tools/setup_check.py
```
**Mac** မှာ `pip` အစား `pip3`, `python` အစား `python3` သုံးပါ။

✅ **စစ်ဆေးချက်** — ဒီလို ပေါ်ရမယ်:
```
✅ token ပုံစံ မှန်တယ်
✅ bot: @your_bot  (id: 8xxxxxxxxxx)
✅ privacy mode ပိတ်ထားတယ် — message အားလုံး ဖတ်နိုင်မယ်
✅ webhook မရှိပါ — polling နဲ့ run လို့ ရတယ်
✅ SQLite ရေးနိုင်/ဖတ်နိုင်တယ်
🎉 အားလုံး အဆင်သင့် ဖြစ်ပါပြီ
```

⚠️ **မအောင်ရင်**

| မက်ဆေ့ချ် | ဘာလုပ်မလဲ |
|---|---|
| `token မမှန်ပါ` | BotFather → `/mybots` → သင့် bot → API Token ပြန်ကူးပါ |
| `privacy mode ဖွင့်နေတယ်` | BotFather → `/setprivacy` → သင့် bot → **Disable** (မဖြစ်မနေ လိုတယ်) |
| `Telegram နဲ့ မချိတ်နိုင်ပါ` | internet စစ်ပါ / VPN ဖွင့်ထားရင် ပိတ်ကြည့်ပါ |
| `ModuleNotFoundError` | `pip install -r requirements.txt` ကို ထပ်ရိုက်ပါ |

---

## အဆင့် ၅ — Bot ကို ကွန်ပျူတာပေါ် ခဏ run ကြည့်

```bash
python bot.py
```

✅ **စစ်ဆေးချက်** — terminal မှာ ဒီလို ပေါ်ရမယ်:
```
🤖 Goii Auto Bot started as @your_bot (8xxxxxxxxxx)
   Default language: my | DB backend: sqlite
```
ပြီးရင် **terminal ကို မပိတ်ပါနဲ့**။ ဖုန်း/Telegram ကနေ စမ်းပါ:
1. `https://t.me/သင့်_bot?startgroup=botstart` နှိပ် → သင့် group ရွေး
2. Group → **Administrators** → bot ကို **right အားလုံး** ပေး
3. Group ထဲမှာ ရိုက်ပါ: `/settings`
4. Button panel ပေါ်လာရမယ် → နှိပ်ပြီး welcome/captcha ဖွင့်ကြည့်ပါ

✅ အားလုံး အလုပ်လုပ်ရင် **အပိုင်း ၂** ဆက်တက်ပါ။
Terminal ပြန်ပိတ်လိုက်ရင် bot ရပ်မယ် — ဒါက ပုံမှန်ပါ (နောက် Render မှာ ၂၄/၇ run မယ်)။

⚠️ **မအောင်ရင်** — group မှာ `/settings` ရိုက်တာ bot မဖြေရင်:
- bot ကို admin ပေးပြီးပြီလား
- privacy mode ပိတ်ပြီးပြီလား (အဆင့် ၄ မှာ စစ်ပြီးသား)
- terminal မှာ error ပေါ်နေလား (အဲ့စာသားကို copy ထားပါ)

---

# အပိုင်း ၂ — GitHub တင်ခြင်း

## အဆင့် ၆ — ပြင်ဆင်ချက်
1. **GitHub account** — [github.com/signup](https://github.com/signup) (မရှိရင် အခမဲ့ ဖွင့်ပါ)
2. **GitHub Desktop** — [desktop.github.com](https://desktop.github.com) (GUI — အလွယ်ဆုံး)
   *CLI ကို ကျွမ်းရင်* → [git-scm.com](https://git-scm.com) က git install လုပ်ပါ

✅ **စစ်ဆေးချက်** — GitHub Desktop မှာ သင့် account နဲ့ sign in ဝင်ထားပြီ

---

## အဆင့် ၇ — Repo တင်

### နည်း (က) — GitHub Desktop (အကြံပြု)
1. GitHub Desktop → **File → Add local repository** → `Desktop\roseplus` ရွေး
   ("not a git repository" ဆိုရင် **create a repository** ကို နှိပ်ပြီး ဆက်ပါ)
2. ဘယ်ဘက်မှာ ပြောင်းထားတဲ့ ဖိုင်တွေ ပေါ်လာမယ် — **`.env` မပါတာ သေချာအောင် စစ်ပါ** (`.gitignore` က ကာကွယ်ပေးထားတယ်)
3. Summary မှာ `Goii Auto Bot bot` ရိုက် → **Commit to main**
4. အပေါ်က **Publish repository** → **Keep this code private** ✅ (private ထားတာ ပိုကောင်း) → **Publish**

### နည်း (ခ) — Command line
```bash
cd Desktop/roseplus
git init
git add .
git commit -m "Goii Auto Bot bot"
git branch -M main
git remote add origin https://github.com/<username>/roseplus.git
git push -u origin main
```
> push လုပ်တဲ့အခါ password အစား **Personal Access Token** တောင်းနိုင်တယ်: GitHub → Settings → Developer settings → Tokens (classic) → Generate new token → `repo` ✅

✅ **စစ်ဆေးချက်** — `github.com/<username>/roseplus` ဖွင့်ရင် ဖိုင်တွေ ပေါ်နေမယ်၊ **`.env` မပါရမယ်**

⚠️ **မအောင်ရင်**
- `repository not found` → repo URL မှန်/မမှန် စစ်ပါ၊ account sign in ဝင်ထားလား
- `.env` ပါသွားမိရင် → ချက်ချင်း ဖျက်ပြီး BotFather → `/revoke` နဲ့ token အသစ် ပြောင်းပါ

---

# အပိုင်း ၃ — Data မပျောက်အောင် Postgres

> Render free မှာ disk မရှိလို့ SQLite file က restart တိုင်း ပျက်မယ်။ ဒါကြောင့် **အခမဲ့ Postgres** တစ်ခု သုံးမယ်။ (ဒီအဆင့်ကို မလုပ်ချင်ရင် ကျော်လို့ရတယ် — ဒါပေမဲ့ deploy တိုင်း setting ပြန်ချိန်ရမယ်)

## အဆင့် ၈ — Supabase (သို့) Neon မှာ database ဖန်တီး

**Supabase (အကြံပြု)**
1. [supabase.com](https://supabase.com) → Sign in (GitHub နဲ့ ဝင်လို့ရ)
2. **New project** → အမည် `roseplus` → database password သတ်မှတ် (**မှတ်ထားပါ**) → region `Southeast Asia (Singapore)` → Create
3. ၂ မိနစ်လောက် စောင့်ပါ (provisioning)
4. **Project Settings → Database → Connection string → URI** ကို copy
   ပုံစံ: `postgresql://postgres:သင့်ပါဝပ်စ်@db.xxxx.supabase.co:5432/postgres`

**Neon (ခြားရွေးချယ်မှု)** — [neon.tech](https://neon.tech) → Create project → Connection string copy

✅ **စစ်ဆေးချက်** — `postgresql://` နဲ့ စတဲ့ စာတန်းရှည်ကြီး တစ်ခု ရပြီ

---

## အဆင့် ၉ — ကွန်ပျူတာကနေ Postgres ကို စမ်း

**Windows PowerShell** (တစ်ကြောင်းတည်း ရိုက်ပါ — quote တွေ အတိအကျ ထားပါ):
```powershell
$env:DATABASE_URL="postgresql://postgres:password@db.xxxx.supabase.co:5432/postgres"
python tools/db_check.py
```
**Mac / Linux**:
```bash
DATABASE_URL="postgresql://..." python tools/db_check.py
```

✅ **စစ်ဆေးချက်** — အဆုံးမှာ ဒီလို ပေါ်ရမယ်:
```
backend: postgres
🎉 Database (postgres) အားလုံး အောင်မြင်ပါတယ်
```

⚠️ **မအောင်ရင်**
| မက်ဆေ့ချ် | ဘာလုပ်မလဲ |
|---|---|
| `password authentication failed` | password မှန်/မမှန် စစ်၊ သို့ Supabase မှာ password reset |
| `Tenant or user not found` | connection string အဟောင်း — ပြန် copy လုပ်ပါ |
| `ModuleNotFoundError: asyncpg` | `pip install asyncpg` |
| timeout / မချိတ်နိုင် | company/university WiFi block ဖြစ်နိုင် — ဖုန်း hotspot စမ်းပါ |

> ဒီစမ်းသပ်မှု အောင်ရင် Render မှာလည်း အောင်မယ်။

---

# အပိုင်း ၄ — Render မှာ တင်ခြင်း

## အဆင့် ၁၀ — Deploy

1. [render.com](https://render.com) → **Sign in with GitHub**
2. **New +** → **Blueprint**
3. `roseplus` repo ရွေး → **Connect**
4. Render က `render.yaml` ကို ဖတ်ပြီး service တစ်ခု ပြင်ဆင်ပေးမယ်။ ဖြည့်ရမယ့် အချက်တွေ:
   - `BOT_TOKEN` = သင့် token
   - `BOT_USERNAME` = သင့် bot username (@ မပါ)
   - `DATABASE_URL` = အဆင့် ၈ က connection string
5. **Apply** → deploy စမယ် (၃–၅ မိနစ်)

> **Blueprint မပေါ်ရင် (နည်း ခ)** — New + → **Web Service** → repo ရွေး → Runtime **Docker** → Instance **Free** → Environment မှာ အထက်ပါ ၃ ခု ထည့် → Create

✅ **စစ်ဆေးချက်** — Render dashboard မှာ status က **Live** ဖြစ်လာမယ်

---

## အဆင့် ၁၁ — Log စစ်ပြီး အလုပ်လုပ်လား ကြည့်

1. Render → သင့် service → **Logs** tab
2. ဒီလို စာတန်း ရှာပါ:
```
🤖 Goii Auto Bot started as @your_bot
   Default language: my | DB backend: postgres
🌐 health server listening on 0.0.0.0:10000
```
3. ဘရောက်ဇာမှာ သင့် URL ဖွင့်ပါ — `https://goii-auto-bot-xxxx.onrender.com`
   → **`Goii Auto Bot is alive`** ပေါ်ရမယ်

✅ ဒီ ၂ ခု တွေ့ရင် **bot က cloud ပေါ်မှာ အလုပ်လုပ်နေပြီ** 🎉

⚠️ **မအောင်ရင်**
| Log မှာ တွေ့ရတာ | ဘာလုပ်မလဲ |
|---|---|
| `BOT_TOKEN မရှိပါ` | Render → Environment → BOT_TOKEN ထည့်ပြီး **Manual Deploy → Restart** |
| `token မမှန်` / `Unauthorized` | token ပြန် copy (အလွတ်နေရာ ပါ/မပါ စစ်) |
| `asyncpg` error | Build log ကြည့် — `pip install` အဆင့် ကျော်သွားနိုင်၊ **Clear build cache & deploy** |
| Build failed | Build log ရဲ့ အနီစာသား ကို copy ယူပြီး ကျွန်တော့်ဆီ ပို့ပါ |
| `Goii Auto Bot is alive` မပေါ် | service Live ဖြစ်ပြီလား၊ URL မှန်/မမှန် စစ် |

---

## အဆင့် ၁၂ — အိပ်မသွားအောင် ping ထားခြင်း (အရေးကြီး)

Render free က **၁၅ မိနစ် request မဝင်ရင် အိပ်တယ်** → bot ရပ်မယ်။

1. [uptimerobot.com](https://uptimerobot.com) → Register (အခမဲ့)
2. **Add New Monitor**
   - Monitor Type: **HTTP(s)**
   - Friendly Name: `Goii Auto Bot`
   - URL: `https://goii-auto-bot-xxxx.onrender.com`
   - Monitoring Interval: **5 minutes**
3. **Create Monitor**

✅ **စစ်ဆေးချက်** — ၁၀ မိနစ်လောက်နေရင် UptimeRobot မှာ **Up** ပြမယ်၊ ပြီးတော့ Telegram မှာ bot က အမြဲ ဖြေနေမယ်

---

# အပိုင်း ၅ — Group မှာ ချိန်ညှိခြင်း

## အဆင့် ၁၃ — Bot ကို သင့်အတိုင်း ချိန်

Group ထဲမှာ ရိုက်ပါ (admin ဖြစ်ရမယ်):

```
/settings
```
Button panel က ပေါ်လာမယ် — နှိပ်ပြီး welcome / captcha / antiflood / antiraid / locks ကို ဖွင့်နိုင်

ပြီးရင် အခြေခံ setting တွေ:
```
/setrules ၁။ ယဉ်ကျေးပါ။ ၂။ Spam/ကြော်ငြာ မလုပ်ပါ။ ၃။ ငွေရေးကြေးရေး မလုပ်ပါ။
/setwelcome မင်္ဂလာပါ {mention}!\n{chatname} ကို ကြိုဆိုပါတယ် 🌸\nRules ကို /rules နဲ့ ဖတ်ပါ။
/captcha on
/captchamode math
/captchakick on
/captchakicktime 10m
/setflood 5
/setfloodmode tmute 10m
/lock url forward
/addblocklist ငွေလဲ
/addblocklist loan
/setwarnlimit 3
/setwarnmode ban
```

✅ **စစ်ဆေးချက်** — စမ်းသပ်ဖို့ dummy account တစ်ခု ဝင်ကြည့်ပါ → welcome + CAPTCHA ပေါ်လား။ `/rules` ရိုက်ရင် rules ပြလား။

---

## အဆင့် ၁၄ — နေ့စဉ် ထိန်းသိမ်းခြင်း (၅ မိနစ်ပဲ)

| ဘာလုပ်မလဲ | ဘယ်လို |
|---|---|
| Setting backup | Group မှာ `/export` → ရလာတဲ့ `.json` ကို သိမ်းထား |
| Setting ပြန်ထည့် | အဲ့ file ကို reply ပြန်ပြီး `/import` |
| Code update | ဖိုင်ပြင်ပြီး GitHub Desktop → Commit → Push → Render အလိုအလျောက် ပြန် deploy |
| Error ကြည့် | Render → Logs |
| Token လုံခြုံရေး | သံသယ ရှိရင် BotFather → `/revoke` → token အသစ် → Render env ပြောင်း |

---

# 📋 အားလုံး ပြီးရင် ဒီစာရင်း အားလုံး ✅ ဖြစ်ရမယ်

- [ ] `python tools/setup_check.py` → အားလုံး ✅ (privacy mode ပိတ်ထား)
- [ ] GitHub repo မှာ code ရှိ၊ **`.env` မပါ**
- [ ] `tools/db_check.py` → `Database (postgres) အားလုံး အောင်မြင်ပါတယ်`
- [ ] Render → status **Live**၊ Logs မှာ `🤖 Goii Auto Bot started`
- [ ] `https://<app>.onrender.com` → `Goii Auto Bot is alive`
- [ ] UptimeRobot → **Up**
- [ ] Telegram group → bot admin၊ `/settings` ဖြေတယ်
- [ ] Welcome + CAPTCHA အလုပ်လုပ်တယ်
- [ ] `/rules`, `/export` အလုပ်လုပ်တယ်

---

# 🆘 ဘယ်အဆင့်မှာ ဘာမှ မဖြစ်ရင်

1. **အဆင့်နံပါတ် + တွေ့ရတဲ့ error စာသား** ကို copy ယူပါ
2. ကျွန်တော့်ဆီ ပို့ပါ — အဲ့ဒီအဆင့်ကို အတိအကျ ဖြေရှင်းပေးပါမယ်

**အများဆုံး တွေ့ရတဲ့ အမှား ၅ ခု**
1. **privacy mode မပိတ်ထား** → locks/blocklist/filters အလုပ်မလုပ်
2. **bot ကို admin မပေး** → ban/mute/delete မလုပ်
3. **`.env` မှာ token မှား/အလွတ်နေရာ ပါ** → `Unauthorized`
4. **DATABASE_URL မထည့်** → deploy တိုင်း setting ပြန်ချိန်ရ
5. **Render sleep** → UptimeRobot မထားမိ → bot ဖြေတာ ရပ်တန့်
