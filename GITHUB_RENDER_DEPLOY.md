# 🚀 GitHub + Render မှာ Deploy လုပ်ခြင်း — တစ်ဆင့်ချိန်း လမ်းညွှန်

**ကြာချိန်** — ပထမဆုံး အကြိမ် ၃၅–၅၀ မိနစ်
**လိုအပ်တာ** — ကွန်ပျူတာ၊ သင့် bot token၊ GitHub account (အခမဲ့)

> လုပ်ရမယ့် အစီအစဉ်
> **① code ယူ ② GitHub Desktop install ③ push ④ Postgres ⑤ Render ⑥ log စစ် ⑦ ping ⑧ Telegram ချိန် ⑨ update လုပ်ပုံ**

---

## အဆင့် ① — Code ကို ကွန်ပျူတာပေါ် ယူ

1. Chat ရဲ့ workspace ထဲက **`roseplus.zip`** ကို ဒေါင်းလုဒ်
2. Desktop ပေါ် ဖြည် (Extract) → `Desktop/roseplus` folder ဖြစ်လာမယ်

✅ **ရလဒ်** — folder ထဲမှာ `bot.py`, `Dockerfile`, `render.yaml`, `locales/`, `plugins/` တွေ ရှိတယ်

> ℹ️ ဒီအဆင့်မှာ `python` install မလိုပါ။ GitHub တင်ဖို့ folder ရှိရုံပါ။

---

## အဆင့် ② — Tool ၂ ခု install

| လိုအပ်တာ | ဘယ်ကနေ |
|---|---|
| **GitHub account** | [github.com/signup](https://github.com/signup) |
| **GitHub Desktop** | [desktop.github.com](https://desktop.github.com) |
| **Render account** | [render.com](https://render.com) — **Sign in with GitHub** နဲ့ ဝင်ပါ |
| **Supabase account** (Postgres အတွက်) | [supabase.com](https://supabase.com) — GitHub နဲ့ ဝင်လို့ရ |

✅ **ရလဒ်** — GitHub Desktop မှာ သင့် account sign in ဝင်ထားပြီ (File → Options → Accounts မှာ တွေ့နိုင်)

---

## အဆင့် ③ — Code ကို GitHub တင် (GitHub Desktop နဲ့)

### ၃.၁ Repo ဖန်တီး
1. GitHub Desktop → menu **File → New repository…**
2. ဖြည့်ပါ:
   - **Name**: `roseplus`
   - **Description**: `Bilingual Telegram group management bot`
   - **Local path**: `C:\Users\<သင့်နာမည်>\Desktop` (Desktop ကို ရွေး — `roseplus` folder ရှိတဲ့ နေရာ)
   - **Initialize**: Git ignore → **None**, License → **None** ✅ (ဘာမှ မရွေးပါ)
3. **Create repository**
4. ဒီအခါ `Desktop\roseplus` folder ကို သင့် files တွေ ထည့်ပါ:
   - `roseplus.zip` ကို ဖြည်ထားတဲ့ folder ထဲက **ဖိုင်အားလုံး** (bot.py, plugins, locales, Dockerfile, render.yaml, …) ကို 
     `Desktop\roseplus` ထဲ ကော်ပီထည့်ပါ (အရင်က ဖန်တီးထားတဲ့ `.git` folder မပါစေနဲ့)

> 💡 အလွယ်ဆုံး — zip ကို `Desktop` မှာ ဖြည်ရင် `Desktop\roseplus` ဖြစ်လာမယ်။ GitHub Desktop မှာ **Add existing repository** ကို သုံးပြီး အဲ့ folder ကို ရွေးပါ။
> ("not a git repository" ဆိုရင် **create a repository** → Create နှိပ်)

### ၃.၂ Commit
1. ဘယ်ဘက်မှာ ဖိုင်တွေ စာရင်း ပေါ်လာမယ် (`bot.py`, `README.md`, …)
2. ⚠️ **`.env` မပါတာ သေချာအောင် စစ်ပါ** (မရှိရင် ကောင်းတယ်)
3. အောက်မှာ **Summary**: `Goii Auto Bot bot` ရိုက် → **Commit to main** နှိပ်

### ၃.၃ Publish
1. အပေါ်က **Publish repository** နှိပ်
2. **Keep this code private** ✅ အမှတ်ခြစ်ထားပါ (ပိုလုံခြုံ)
3. **Publish repository**

✅ **ရလဒ်** — `github.com/<username>/roseplus` ဖွင့်ကြည့်ရင် ဖိုင်တွေ ပေါ်နေမယ်၊ **`.env` မပါ**

⚠️ **မအောင်ရင်**
- `Publish` မတွေ့ရင် → `File → Options → Accounts` မှာ sign in ဝင်ပါ
- push error → internet/proxy စစ်ပါ၊ ပြီး **Repository → Push origin** ထပ်
- `.env` တင်မိသွားရင် → GitHub မှာ ဖိုင်ဖျက်ပြီး **BotFather → /revoke** နဲ့ token အသစ် ပြောင်း

---

## အဆင့် ④ — အခမဲ့ Postgres (data မပျောက်ဖို့)

> Render free မှာ disk မရှိလို့ SQLite က restart တိုင်း ပျက်မယ်။ ဒါကို မလုပ်ရင် deploy တိုင်း setting ပြန်ချိန်ရမယ်။

1. [supabase.com](https://supabase.com) → **New project**
2. ဖြည့်ပါ:
   - Name: `roseplus`
   - Database Password: ခိုင်မာတဲ့ စကားဝှက် → **မှတ်ထားပါ**
   - Region: **Southeast Asia (Singapore)**
3. **Create new project** → ၁–၂ မိနစ် စောင့်
4. **Project Settings → Database → Connection string → URI** ကို copy:
```
postgresql://postgres:YOURPASSWORD@db.xxxxxxxx.supabase.co:5432/postgres
```
   စကားဝှက် နေရာမှာ သင့်ဟာ ဖြစ်နေရမယ် (အလွတ်နေရာ/`[YOUR-PASSWORD]` မပါရ)

✅ **ရလဒ်** — `postgresql://` နဲ့ စတဲ့ စာတန်းရှည် တစ်ကြောင်း ရပြီ (မှတ်ထား / notepad မှာ သိမ်းထား)

---

## အဆင့် ⑤ — Render မှာ Deploy

### ၅.၁ Blueprint နဲ့ တင် (အကြံပြု — `render.yaml` ပါပြီးသား)
1. [dashboard.render.com](https://dashboard.render.com) → **New +** → **Blueprint**
2. **Connect GitHub** → `roseplus` repo ရွေး → **Connect**
3. Render က `render.yaml` ကို ဖတ်ပြီး service ပြင်ဆင်ပြီးသားဖြစ်မယ်။ ဖြည့်ရမယ့် **Environment Variables**:
   | Key | Value |
   |---|---|
   | `BOT_TOKEN` | သင့် token (`123456789:AAH…`) |
   | `BOT_USERNAME` | သင့် bot username (**@ မပါ**) |
   | `DATABASE_URL` | အဆင့် ④ က `postgresql://…` |
   | `DEFAULT_LANG` | `my` (မြန်မာ) / `en` |
4. **Apply** → deploy စမယ် (၃–၆ မိနစ်)

### ၅.၂ Blueprint မပေါ်ရင် (Manual)
1. **New +** → **Web Service** → `roseplus` repo → **Connect**
2. **Name**: `goii-auto-bot`
3. **Language/Runtime**: **Docker** (repo ထဲက `Dockerfile` ကို အလိုအလျောက် သုံးမယ်)
4. **Instance Type**: **Free**
5. **Environment Variables** — ၅.၁ က ဇယားအတိုင်း ထည့်
6. **Create Web Service**

> ℹ️ `PORT` ကို Render ကိုယ်တိုင် ပေးတယ် — ထည့်စရာ မလိုပါ။ Bot က အဲ့ port မှာ HTTP server ဖွင့်ပြီး `Goii Auto Bot is alive` ပြန်ပေးတယ်။

✅ **ရလဒ်** — Render dashboard မှာ service က **Building → Deploying → Live** ဖြစ်လာမယ်

---

## အဆင့် ⑥ — Log စစ်ဆေး (အရေးအကြီးဆုံး အဆင့်)

1. Render → သင့် service → **Logs** tab
2. ဒီ ၂ ကြောင်း ရှာပါ:
```
🤖 Goii Auto Bot started as @your_bot (8xxxxxxxxxx)
   Default language: my | DB backend: postgres
🌐 health server listening on 0.0.0.0:10000
```
3. Browser မှာ သင့် URL ဖွင့် — `https://goii-auto-bot-xxxx.onrender.com`
   → **`Goii Auto Bot is alive`** ပေါ်ရမယ်

✅ **ဒီ ၂ ခု ရရင် bot က cloud ပေါ် ၂၄ နာရီ အလုပ်လုပ်နေပြီ** 🎉

⚠️ **မအောင်ရင် — Log ထဲက စာသားနဲ့ ဖြေရှင်းနည်း**

| Log / အခြေအနေ | အကြောင်းရင်း | ဖြေရှင်းနည်း |
|---|---|---|
| `BOT_TOKEN မရှိပါ` | env မထည့်ရသေး | Environment → `BOT_TOKEN` ထည့် → **Manual Deploy → Restart** |
| `Unauthorized` / `token မမှန်` | token မှား / အလွတ်နေရာ ပါ | token ပြန် copy၊ `BotFather → API Token` |
| `asyncpg` / `ModuleNotFoundError` | build cache | **Clear build cache & deploy** |
| `password authentication failed` | Supabase စကားဝှက် မှား | connection string ပြန် copy (password အစစ် ပါရမယ်) |
| `no open ports detected` | PORT မဖတ်နိုင် | Environment မှာ `PORT` မထည့်ထားမှန်း စစ် (Render ကိုယ်တိုင် ပေးတယ်) |
| Build failed (အနီ) | ဖိုင် မပြည့်စုံ | repo ထဲ `Dockerfile`, `requirements.txt`, `bot.py` ရှိမရှိ စစ် |
| Live ဖြစ်ပြီး bot မဖြေ | sleep ဖြစ်နေ | အဆင့် ⑦ |

> Log ထဲက အနီစာသားကို copy ပြီး ကျွန်တော့်ဆီ ပို့ပါ — အတိအကျ ဖြေရှင်းပေးပါမယ်။

---

## အဆင့် ⑦ — အိပ်မသွားအောင် ping ထားခြင်း

Render free က **၁၅ မိနစ် request မဝင်ရင် အိပ်တယ်** → bot က ခေတ္တ ရပ်မယ်။

1. [uptimerobot.com](https://uptimerobot.com) → **Register for FREE**
2. **+ Add New Monitor**
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: `Goii Auto Bot`
   - **URL**: `https://goii-auto-bot-xxxx.onrender.com`
   - **Monitoring Interval**: **5 minutes**
3. **Create Monitor**

✅ **ရလဒ်** — ၁၀ မိနစ်အတွင်း dashboard မှာ **Up** (အစိမ်း) ပြမယ်

> ℹ️ Render free မှာ **750 နာရီ/လ** ရှိတာမို့ service တစ်ခုပဲ ထားပါ။

---

## အဆင့် ⑧ — Telegram မှာ ချိန်ညှိ

1. Group → **Administrators** → bot ကို ထည့် → **right အားလုံး** ပေး
2. Group ထဲမှာ ရိုက်ပါ —
```
/settings
```
   → button panel ပေါ်လာရမယ် (welcome / captcha / antiflood / antiraid / locks)
3. အခြေခံ setting:
```
/setrules ၁။ ယဉ်ကျေးပါ။ ၂။ Spam/ကြော်ငြာ မလုပ်ပါ။ ၃။ ငွေရေးကြေးရေး မလုပ်ပါ။
/setwelcome မင်္ဂလာပါ {mention}!\n{chatname} ကို ကြိုဆိုပါတယ် 🌸\n/rules နဲ့ rules ဖတ်ပါ။
/captcha on
/captchamode math
/captchakick on
/setflood 5
/setfloodmode tmute 10m
/lock url forward
/addblocklist ငွေလဲ
```
4. Backup ယူထားပါ: `/export`

✅ **ရလဒ်** — member အသစ် ဝင်ရင် welcome + CAPTCHA ပေါ်တယ်၊ `/rules` အလုပ်လုပ်တယ်

---

## အဆင့် ⑨ — နောက်ပိုင်း ပြင်ချင်ရင် (Update)

```text
ဖိုင် ပြင်ပါ → GitHub Desktop ဖွင့် → Summary ရိုက် → Commit to main → Push origin
```
→ Render က **အလိုအလျောက် ပြန် deploy** လုပ်မယ် (`autoDeploy: true`)

| ပြင်ချင်တာ | ဖိုင် |
|---|---|
| စာသား (မြန်မာ/အင်္ဂလိပ်) | `locales/my.json`, `locales/en.json` |
| ဘာသာစကား အသစ် | `locales/<code>.json` ထပ်ထည့် (key တွေ တူရမယ်) |
| Command အသစ် | `plugins/` ထဲက သင့်ဖိုင် |
| Default setting | `db.py` ရဲ့ SCHEMA defaults |

---

## ✅ Deploy အောင်မြင်ခြင်း စာရင်း

- [ ] GitHub repo မှာ code ရှိ၊ `.env` မပါ
- [ ] Render status **Live**
- [ ] Logs မှာ `🤖 Goii Auto Bot started` + `DB backend: postgres`
- [ ] `https://<app>.onrender.com` → `Goii Auto Bot is alive`
- [ ] UptimeRobot → **Up**
- [ ] Telegram: bot admin၊ `/settings` ဖြေတယ်
- [ ] Welcome + CAPTCHA အလုပ်လုပ်တယ်
- [ ] `/export` နဲ့ backup ယူထားပြီ

---

## 🆘 အများဆုံး ကြုံရတဲ့ ပြဿနာ ၅ ခု

1. **Bot က group မှာ မဖြေ** → bot admin မဟုတ် / privacy mode မပိတ်
2. **Deploy ပြီး ချက်ချင်း crash** → `BOT_TOKEN` env မထည့် / မှား
3. **Restart တိုင်း setting ပျောက်** → `DATABASE_URL` မထည့်
4. **ညဘက် bot မဖြေ** → Render sleep (UptimeRobot မထားမိ)
5. **`password authentication failed`** → Supabase connection string မှာ password မှား
