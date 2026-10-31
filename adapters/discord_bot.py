"""Discord adapter. Run from repo root:  python -m adapters.discord_bot"""

import os

import discord
from dotenv import load_dotenv

from core.logic import NayEngine, load_insults, parse_ids

load_dotenv()

engine = NayEngine(
    owner_id=int(os.environ["DISCORD_OWNER_ID"]),
    targets=parse_ids(os.getenv("DISCORD_TARGETS")),
    insults=load_insults(),
    window_sec=int(os.getenv("WINDOW_SEC", 600)),
    cooldown_sec=int(os.getenv("COOLDOWN_SEC", 60)),
)

intents = discord.Intents.default()
intents.message_content = True   # also enable this in the Developer Portal
client = discord.Client(intents=intents)


@client.event
async def on_ready():
    print(f"NAY bot (Discord) running as {client.user}")


@client.event
async def on_message(message: discord.Message):
    if message.author.bot or not message.content:
        return

    reply_to_id = reply_to_sender = None
    ref = message.reference
    if ref and ref.message_id:
        reply_to_id = ref.message_id
        ref_msg = ref.resolved if isinstance(ref.resolved, discord.Message) else None
        if ref_msg is None:
            try:
                ref_msg = await message.channel.fetch_message(ref.message_id)
            except discord.HTTPException:
                ref_msg = None
        if ref_msg:
            reply_to_sender = ref_msg.author.id

    response = engine.on_message(
        chat_id=message.channel.id,
        msg_id=message.id,
        sender_id=message.author.id,
        text=message.content,
        reply_to_msg_id=reply_to_id,
        reply_to_sender_id=reply_to_sender,
        sender_name=message.author.display_name,
    )
    if response:
        await message.reply(response)


if __name__ == "__main__":
    client.run(os.environ["DISCORD_TOKEN"])
