"""Telegram adapter. Run from repo root:  python -m adapters.telegram_bot"""

import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

from core.logic import NayEngine, load_insults, parse_ids

load_dotenv()

engine = NayEngine(
    owner_id=int(os.environ["TELEGRAM_OWNER_ID"]),
    targets=parse_ids(os.getenv("TELEGRAM_TARGETS")),
    insults=load_insults(),
    window_sec=int(os.getenv("WINDOW_SEC", 600)),
    cooldown_sec=int(os.getenv("COOLDOWN_SEC", 60)),
)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not msg.text or not msg.from_user or msg.from_user.is_bot:
        return
    reply = msg.reply_to_message
    response = engine.on_message(
        chat_id=msg.chat_id,
        msg_id=msg.message_id,
        sender_id=msg.from_user.id,
        text=msg.text,
        reply_to_msg_id=reply.message_id if reply else None,
        reply_to_sender_id=reply.from_user.id if reply and reply.from_user else None,
        sender_name=msg.from_user.first_name or "bro",
    )
    if response:
        await msg.reply_text(response)


def main():
    app = ApplicationBuilder().token(os.environ["TELEGRAM_TOKEN"]).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("NAY bot (Telegram) running...")
    app.run_polling()


if __name__ == "__main__":
    main()
