# NAY bot — Not Asking You

A Telegram + Discord bot that calls out people who answer questions meant for you.

## How it decides
1. You send a message.
2. Someone **replies** to it with a question → the question is "open".
3. Someone else **replies** to that question before you do → NAY.

Questions sent to you out of nowhere ("u eat?") are ignored, so anyone can answer those.
Questions close when you reply, or expire after `WINDOW_SEC`. `COOLDOWN_SEC` stops spam.

## Setup
```
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # fill in tokens + IDs
```
- Telegram: BotFather → `/setprivacy` → Disable, so the bot can read group messages.
- Discord: enable **Message Content Intent** in the Developer Portal.

## Run
```
python -m adapters.telegram_bot
python -m adapters.discord_bot
pytest
```

## Structure
- `core/logic.py` — platform-independent rules (question detection, open questions, NAY decision)
- `adapters/` — thin Telegram and Discord wrappers
- `insults.txt` — your responses, `{name}` = whoever answered for you

## Roadmap
- Replace rule-based `is_question()` with a small ML classifier
