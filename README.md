# Claude Telegram Calendar Bot

A personal family calendar assistant on Telegram, powered by Claude Haiku and Google Calendar. Supports natural language queries, calendar writes (create/update/delete events), task management, and web search — all from a Telegram chat.

Built and described in: *[I Built This Before Anthropic Did — and That Taught Me When to Build at All](#)* (Medium, 2026)

---

## What it does

- **Natural language calendar queries** — "what's on this week?", "when is the next dentist appointment?"
- **Calendar writes** — create, update, and delete events with a confirmation step before anything executes
- **Task management** — create and complete Google Tasks
- **Multi-user** — primary user gets full access (all calendars + tasks); family members get read-only access to the shared family calendar
- **Web search** — location queries, travel times, and recommendations via Claude's web search tool
- **Security** — input injection detection, output anomaly filter, kill switch, and Telegram ID whitelist

---

## Prerequisites

- Python 3.11+
- A Google Cloud project with the Calendar API and Tasks API enabled
- A Google OAuth 2.0 client (Desktop app type) — download `credentials.json`
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- An Anthropic API key from [console.anthropic.com](https://console.anthropic.com)

---

## Setup

### 1. Clone and create a virtual environment

```bash
git clone https://github.com/YOUR_USERNAME/Claude-telegram-bot.git
cd Claude-telegram-bot
python -m venv venv

# Windows (Git Bash)
source venv/Scripts/activate

# macOS / Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Google OAuth credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com) → APIs & Services → Credentials
2. Create an OAuth 2.0 Client ID (Desktop app)
3. Download and save as `credentials.json` in the project root

Enable these APIs in your project:
- Google Calendar API
- Google Tasks API

> **Note:** If your OAuth app is in Testing mode, tokens expire every 7 days. Publish the app to Production to remove this limit.

### 3. Configure secrets

```bash
cp .env.example .env
```

Edit `.env` and fill in:
- `TELEGRAM_BOT_TOKEN` — from @BotFather
- `PRIMARY_USER_TELEGRAM_ID` — your Telegram user ID (message [@userinfobot](https://t.me/userinfobot) to find it)
- `PARTNER_TELEGRAM_ID` — optional partner/secondary user ID
- `ANTHROPIC_API_KEY` — from console.anthropic.com

### 4. Configure personal settings

```bash
cp telegram_bot/config.yaml.example telegram_bot/config.yaml
```

Edit `telegram_bot/config.yaml` and fill in:
- Your timezone (IANA format, e.g. `Asia/Singapore`, `Europe/London`)
- Your Google Calendar IDs (find these in Google Calendar → Settings → click a calendar)
- Display names and calendar prefixes for each family member
- The env var names for each user's Telegram ID (must match what you put in `.env`)

### 5. First-time authentication

On first run, a browser window will open for Google OAuth consent. After completing the flow, `token.json` and `token_tasks.json` are saved automatically — subsequent runs are silent.

```bash
source venv/Scripts/activate
python src/auth.py  # or just start the bot — it will trigger auth if needed
```

### 6. Start the bot

**Windows (Git Bash):**
```bash
bash telegram_bot/bot_runner.sh
```

**Manually:**
```bash
source venv/Scripts/activate
cd telegram_bot
python telegram_bot.py
```

The bot runs on your local machine. It must be running for Telegram messages to be received.

---

## Project structure

```
Claude-telegram-bot/
├── telegram_bot/
│   ├── telegram_bot.py       # Main bot — routing, Haiku API calls, tool-calling loop
│   ├── config_loader.py      # Loads config.yaml, exposes typed constants
│   ├── config.yaml           # Gitignored — your personal config
│   ├── config.yaml.example   # Template
│   └── bot_runner.sh         # Startup script (kills stale instances, starts bot)
├── src/
│   ├── auth.py               # Google OAuth2 flow and token management
│   ├── calendar_client.py    # Google Calendar API wrapper
│   ├── query_calendar.py     # Calendar read CLI
│   ├── write_calendar.py     # Calendar write CLI (create/update/delete)
│   ├── tasks_client.py       # Google Tasks API wrapper
│   └── tasks_cli.py          # Tasks CLI (list/create/complete)
├── logs/                     # Gitignored — runtime logs
├── memory/                   # Gitignored — optional Claude Code context files
├── .env                      # Gitignored — your secrets
├── .env.example              # Template
├── credentials.json          # Gitignored — Google OAuth client credentials
├── token.json                # Gitignored — Calendar OAuth token (auto-saved)
├── token_tasks.json          # Gitignored — Tasks OAuth token (auto-saved)
└── requirements.txt
```

---

## Architecture notes

- **Model:** Claude Haiku (`claude-haiku-4-5-20251001`) for all natural language queries — fast and cheap (~$0.008/message with tool calling)
- **Routing:** Stages 1–8a are hardcoded (auth, security checks, task routing); stage 8b+ uses a Haiku tool-calling loop for calendar queries and writes
- **Calendar tools:** `query_calendar`, `query_tasks`, `create_event`, `update_event`, `delete_event` (max 8 tool-call rounds per message)
- **Write confirmation:** Haiku proposes a write → user confirms with "yes" → `write_calendar.py --confirm` executes
- **Conversation memory:** 6-turn rolling window per user, in-memory (resets on bot restart)
- **Security:** Input injection pattern check, output anomaly filter, weighted kill switch, Telegram ID whitelist

---

## Cost

At typical personal usage (a few queries per day):
- ~$0.002 per simple query (single Haiku call)
- ~$0.008 per query using the tool-calling loop (3–4 rounds)
- Estimated $0.50–$2/month total

---

## Security notes

- All calendar and task data is tagged as untrusted external input — event descriptions are never treated as instructions
- Telegram ID whitelist — unknown users are silently ignored; the primary user receives an alert after 3 messages from an unknown ID
- Kill switch — weighted security event counter; if threshold is reached within 5 minutes, the primary user is alerted and the bot shuts down
- OAuth tokens are stored unencrypted at rest — keep your machine's filesystem access controlled

---

## Licence

MIT
