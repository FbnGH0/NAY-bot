# NAY bot — Not Asking You

A Telegram + Discord bot that calls out people who answer questions meant for someone else.

## How it decides
1. Person A sends a message.
2. Person B **replies** to it with a question → the question is "open" for A.
3. Person C **replies** to that question before A does → NAY C.

Works for everyone in the chat. Questions out of nowhere ("u eat?") are ignored.
`TELEGRAM_TARGETS` limits who can be NAY'd; empty = anyone. Questions close when the
right person replies, or expire after `WINDOW_SEC`. `COOLDOWN_SEC` stops spam.

## Commands (anyone can use them, once per minute each)
- Reply `/nay` to someone's message to NAY them manually (not yourself or the bot).
- Reply `/wrongnay` to one of the bot's NAYs to mark it as wrong.

Every NAY is logged to `data/nays.jsonl` with the 15 messages before it, plus who used
the command. Wrong NAYs are logged with `"source": "wrong"` and the same `nayed_msg_id`,
so they can be matched to the original NAY and used as negative examples for the ML version.

## Setup

### 1. Install
```
git clone <this repo>
cd NAY-bot
python -m venv venv
venv\Scripts\activate           # Mac/Linux: source venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # Mac/Linux: cp .env.example .env
```

### 2. Create your Telegram bot
1. In Telegram, open a chat with **@BotFather** and send `/newbot`.
2. Pick a display name (e.g. `NAY bot`) and a username ending in `bot` (e.g. `my_nay_bot`).
3. BotFather replies with a **token** like `123456789:ABCdef...`. Put it in `.env`:
   ```
   TELEGRAM_TOKEN=123456789:ABCdef...
   ```
   Treat the token like a password. If it leaks, send `/revoke` to BotFather to get a new one.
4. Send `/setprivacy` to BotFather, pick your bot, and choose **Disable**.
   Without this, the bot only sees commands in groups, not normal messages.
5. Add the bot to your **group**: open the group → Add Members → search your bot's username.
   If the bot was added before you disabled privacy mode, remove it and add it again.

> Works in groups and supergroups only. In channels, messages are sent as the channel,
> so the bot can't tell who sent what.

### 3. (Optional) Limit who can be NAY'd
Leave `TELEGRAM_TARGETS` empty to NAY anyone. To NAY only certain people, add their
user IDs, comma-separated, no spaces or quotes:
```
TELEGRAM_TARGETS=111111111,222222222
```
To find a user ID, forward one of their messages to **@userinfobot**
(or message it yourself to get your own).

### 4. (Optional) Settings
All optional. Missing settings use the defaults shown.
```
WINDOW_SEC=604800             # how long a question stays open (default 600 = 10 min)
COOLDOWN_SEC=60               # min gap between auto NAYs per chat (0 = off)
NAY_COMMAND_COOLDOWN_SEC=60   # min gap between /nay uses per person (0 = off)
```
Deleting a line does **not** turn it off; it falls back to the default. Set it to `0` instead.

### 5. Your insults
Edit `insults.txt`, one per line. `{name}` becomes the name of whoever got NAY'd.
Lines starting with `#` are ignored.

### Discord (optional)
1. Go to https://discord.com/developers/applications → **New Application**.
2. **Bot** tab → **Reset Token** → copy it into `DISCORD_TOKEN` in `.env`.
   On the same page, turn on **Message Content Intent**.
3. **OAuth2 → URL Generator** → tick `bot`, then **View Channels**, **Send Messages**,
   **Read Message History** → open the link and add the bot to your server.
4. For user IDs: Settings → Advanced → Developer Mode on, then right-click a user → Copy User ID.

Discord bots only work in servers, not group DMs. `/nay` and `/wrongnay` are Telegram-only for now.

## Run
```
python -m adapters.telegram_bot    # Telegram
python -m adapters.discord_bot     # Discord (separate terminal)
pytest                             # tests
```
You should see `NAY bot (Telegram) running...`. Keep the terminal open; Ctrl+C stops it.
Restart after changing code or `.env`. Only run **one** copy per token, or Telegram
will return a "Conflict" error.

### Troubleshooting
- **Bot ignores normal messages** → privacy mode is still on (step 2.4), or re-add the bot.
- **`/nay` does nothing** → reply to a message with it; check the cooldown; check the terminal.
- **`httpx.ConnectError` / NetworkError** → your network is blocking Telegram. Try another network.
  NAYs are logged before sending, so no data is lost.
- **`KeyError: 'TELEGRAM_TOKEN'`** → `.env` is missing, misnamed (`.env.txt`), or not in the project folder.

## Structure
- `core/logic.py` — platform-independent rules (question detection, open questions, NAY decision)
- `adapters/` — thin Telegram and Discord wrappers
- `core/nay_log.py` — appends every NAY to `data/nays.jsonl`
- `insults.txt` — your responses, `{name}` = whoever answered for you
- `tests/` — pytest tests for the core logic

`.env` and `data/` are git-ignored: they hold your token and your friends' messages.

## Roadmap
- Train an ML model to detect answers that aren't direct replies, using the logged NAYs
- `!nay` / `!wrongnay` and logging for Discord
- Deploy to the cloud for 24/7 uptime
