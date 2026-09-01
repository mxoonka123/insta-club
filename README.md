# INSTA CLUB

Closed business community in Serbia for entrepreneurs and content creators.

This repository is the Telegram bot that runs the club: applications, curator payments, membership, catalog, knowledge base, and monthly meetings (Belgrade / Novi Sad / online).

The GitHub repository is [insta-club](https://github.com/mxoonka123/insta-club). **The product is INSTA CLUB.**

Stack: Python 3.13, [aiogram 3](https://docs.aiogram.dev/), SQLite.

---

## Why members disappear after deploy

The bot **does** have a database (SQLite). On Railway the container disk is temporary. A Redeploy starts a new container, so `instaclub.db` is empty unless it lives on a **Volume**.

That is why the admin panel showed 0 members after an update — not because the club logic was wiped, but because the file was not persistent.

**Fix once in Railway (required for production):**

1. Open the bot service → **Volumes** → **Add Volume**
2. Mount path: `/data`
3. Variables: `DB_PATH=/data/instaclub.db`
4. **Redeploy**

If the volume is missing, organizers get a warning in Telegram at startup and a red note in the admin panel (`админ`).

If you already stored data in `/data/profiles.db`, the bot keeps using that file so nothing is abandoned.

---

## Product

**Tariff START — 19 € / month**

- Instagram support
- closed business community
- one club meeting per month (offline Belgrade, offline Novi Sad, or online)
- one 30-minute Welcome review in month 1

Organizers choose the meeting format each month. The promise to members is one meeting per month, not “always offline in one city”.

### Member journey

```text
/start
  → application (name, city, business, Instagram, goal)
  → pay the curator, then «Я оплатил»
  → organizer taps Одобрить
  → club menu
```

Club menu: community, knowledge base, meetings, subscription, referral, profile.

### Organizer journey

Type **админ** in the bot. Organizer IDs: `ADMIN_IDS` plus `318427459` (always included in the bot).

| Button | Action |
|---|---|
| Заявки | approve / reject applications |
| Участники | list members, renew or revoke access |
| Найти | name, @username, or Telegram ID |
| Все встречи | upcoming and past, RSVP list |
| Новая встреча | publish a meeting (broadcast + reminders) |
| Статистика | club numbers |
| Выйти из админки | back to the normal menu |

«Я оплатил» is pressed by the **member**. **Одобрить** is the organizer confirming payment and opening access. There is no separate “mark as paid” button.

Kicked members see the welcome screen again and can apply from scratch.

---

## Demo for a reviewer

1. Open the live bot in Telegram (ask the owner for the `@` username).
2. `/start` → walk through the application as a new member.
3. In a second account (organizer): type `админ` → **Заявки** → **Одобрить**.
4. Back on the member account: club menu, **Встречи клуба**.
5. Organizer: **Новая встреча** (date like `12.09.2026`) → publish. Member gets the announcement.

Do not enable `SEED_DEMO=1` on the production Railway service.

---

## Environment variables

Copy `.env.example` to `.env` locally. Never commit `.env` (the bot token lives there).

| Variable | Required | Example | Meaning |
|---|---|---|---|
| `BOT_TOKEN` | yes | `123456:ABC...` | from [@BotFather](https://t.me/BotFather) |
| `ADMIN_IDS` | yes | `318427459` | organizer Telegram IDs, comma-separated. Get ID from [@userinfobot](https://t.me/userinfobot) — digits, not `@username` |
| `CURATOR_USERNAME` | yes | `ljudmila_solo` | curator nick without `@` |
| `BUSINESS_PRICE` | no | `19 € / месяц` | price on the tariff screen |
| `PAYMENT_DETAILS` | no | payment text | shown after the application |
| `DB_PATH` | **yes on Railway** | `/data/instaclub.db` | SQLite file on the Volume |
| `BOT_USERNAME` | no | filled automatically | referral links |
| `SEED_DEMO` | no | `1` | demo catalog cards only if the database is empty |

---

## Run locally

Python 3.10+. Use **either** local polling **or** Railway — the same `BOT_TOKEN` cannot run in two places at once.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env               # Windows: Copy-Item .env.example .env
```

Put `BOT_TOKEN` and `ADMIN_IDS` into `.env`, then:

```bash
python -m bot.main
```

Local SQLite file: `instaclub.db` in the project folder (gitignored).

---

## Railway

1. Service is connected to this GitHub repo: push to `main` deploys INSTA CLUB.
2. **Variables** — same keys as the table above.
3. **Volume** — mount `/data`, `DB_PATH=/data/instaclub.db` (see the warning at the top).
4. Start command is already in `railway.toml`: `python -m bot.main`.

After a merge to `main`, wait for the deploy to finish, then type `админ` in Telegram. If the Volume is missing, the bot will say so.

---

## Repository layout

```text
bot/
  main.py            start, SQLite, meeting reminders
  config.py          env + where the database file lives
  database.py        members, payments, meetings
  texts.py           copy members see
  keyboards.py       buttons
  states.py          application + meeting wizard
  meetings.py        dates (Europe/Belgrade) and formatting
  reminders.py       24h and 2h reminders
  notify.py          messages to organizers
  helpers.py         cards, access checks
  handlers/
    start.py         /start, tariffs, partners
    onboarding.py    application
    payment.py       «Я оплатил»
    admin.py         organizer panel
    events.py        meetings
    community.py     catalog
    knowledge.py     knowledge base
    subscription.py  tariff
    referral.py      invite a friend
    profile.py       profile
```

Change member-facing wording in `bot/texts.py`. Change buttons in `bot/keyboards.py`.

---

## Intentional limits

- SQLite, not PostgreSQL (one file; must sit on a Railway Volume)
- Dialog state is in process memory (an unfinished application resets after restart — `/start` again)
- Payment is via the curator, not Stripe
- Organizers work inside Telegram, there is no web admin
