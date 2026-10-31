"""Telegram adapter. Run from repo root:  python -m adapters.telegram_bot"""

import asyncio
import os
import time
from collections import defaultdict, deque

from dotenv import load_dotenv
from telegram import Update
from telegram.error import NetworkError
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes,
                          MessageHandler, filters)

from core.logic import NayEngine, load_insults, parse_ids
from core.nay_log import log_nay

load_dotenv()

engine = NayEngine(
    targets=parse_ids(os.getenv("TELEGRAM_TARGETS")),
    insults=load_insults(),
    window_sec=int(os.getenv("WINDOW_SEC", 600)),
    cooldown_sec=int(os.getenv("COOLDOWN_SEC", 60)),
)

COMMAND_COOLDOWN = int(os.getenv("NAY_COMMAND_COOLDOWN_SEC", 60))
last_command_use = {}   # user_id -> when they last used /nay or /wrongnay


def on_cooldown(user_id):
    """Per-person cooldown for commands, so nobody can spam them."""
    now = time.time()
    if now - last_command_use.get(user_id, 0) < COMMAND_COOLDOWN:
        return True
    last_command_use[user_id] = now
    return False


# Last 100 messages per chat, so we can save the 15 before any NAY'd message
recent = defaultdict(lambda: deque(maxlen=100))


def remember(msg):
    recent[msg.chat_id].append({
        "id": msg.message_id,
        "sender_id": msg.from_user.id,
        "sender_name": msg.from_user.first_name,
        "text": msg.text,
        "reply_to": msg.reply_to_message.message_id if msg.reply_to_message else None,
        "time": msg.date.timestamp(),
    })


def context_before(chat_id, msg_id, n=15):
    """The n messages before msg_id. Falls back to the latest n if not found."""
    msgs = list(recent[chat_id])
    for i, m in enumerate(msgs):
        if m["id"] == msg_id:
            return msgs[max(0, i - n):i]
    return msgs[-n:]


async def send_reply(message, text, retries=2):
    """Reply, retrying a couple of times if the network blips."""
    for attempt in range(retries + 1):
        try:
            return await message.reply_text(text)
        except NetworkError as e:
            if attempt == retries:
                print(f"Couldn't send NAY after {retries + 1} tries: {e}")
                return None
            await asyncio.sleep(2)


async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not msg.text or not msg.from_user or msg.from_user.is_bot:
        return
    if msg.forward_origin:
        return
    remember(msg)

    reply = msg.reply_to_message
    replied_user = reply.from_user if reply else None
    response = engine.on_message(
        chat_id=msg.chat_id,
        msg_id=msg.message_id,
        sender_id=msg.from_user.id,
        text=msg.text,
        reply_to_msg_id=reply.message_id if reply else None,
        reply_to_sender_id=replied_user.id if replied_user and not replied_user.is_bot else None,
        sender_name=msg.from_user.first_name or "bro",
    )
    if response:
        # Log first, so a network error never loses the data
        log_nay(platform="telegram", source="auto", chat_id=msg.chat_id,
                nayed_msg_id=msg.message_id,
                nayed_id=msg.from_user.id, nayed_name=msg.from_user.first_name,
                answer_text=msg.text,
                question_text=reply.text if reply else None,
                context_msgs=context_before(msg.chat_id, msg.message_id))
        await send_reply(msg, response)


async def nay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Anyone replies /nay to someone's message -> NAY them and log it."""
    msg = update.effective_message
    if not msg or not msg.from_user:
        return
    target = msg.reply_to_message
    if not target or not target.from_user:
        await send_reply(msg, "Reply to someone's message with /nay")
        return
    if target.from_user.is_bot or target.from_user.id == msg.from_user.id:
        return                                   # can't NAY bots or yourself
    if not engine.can_nay(target.from_user.id):
        await send_reply(msg, "They're not on the target list")
        return
    if on_cooldown(msg.from_user.id):
        return

    question = target.reply_to_message
    log_nay(platform="telegram", source="manual", chat_id=msg.chat_id,
            nayer_id=msg.from_user.id, nayer_name=msg.from_user.first_name,
            nayed_msg_id=target.message_id,
            nayed_id=target.from_user.id, nayed_name=target.from_user.first_name,
            answer_text=target.text,
            question_text=question.text if question else None,
            context_msgs=context_before(msg.chat_id, target.message_id))
    await send_reply(target, engine.pick_insult(target.from_user.first_name or "bro"))


async def wrongnay_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Anyone replies /wrongnay to one of the bot's NAY messages -> mark it wrong.

    The bot's NAY is a reply to the NAY'd message, so we log that message's id.
    In training, match it to the original NAY with (chat_id, nayed_msg_id).
    """
    msg = update.effective_message
    if not msg or not msg.from_user:
        return
    bot_msg = msg.reply_to_message
    if (not bot_msg or not bot_msg.from_user
            or bot_msg.from_user.id != context.bot.id or not bot_msg.reply_to_message):
        await send_reply(msg, "Reply to one of my NAYs with /wrongnay")
        return

    if on_cooldown(msg.from_user.id):
        return

    nayed = bot_msg.reply_to_message
    log_nay(platform="telegram", source="wrong", chat_id=msg.chat_id,
            flagged_by_id=msg.from_user.id, flagged_by_name=msg.from_user.first_name,
            bot_msg_id=bot_msg.message_id,
            nayed_msg_id=nayed.message_id,
            nayed_id=nayed.from_user.id if nayed.from_user else None,
            answer_text=nayed.text)
    await send_reply(bot_msg, "My bad, noted as a wrong NAY.")


def main():
    app = ApplicationBuilder().token(os.environ["TELEGRAM_TOKEN"]).build()
    app.add_handler(CommandHandler("nay", nay_command))
    app.add_handler(CommandHandler("wrongnay", wrongnay_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("NAY bot (Telegram) running...")
    app.run_polling()


if __name__ == "__main__":
    main()
