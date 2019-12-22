import collections
import logging
import os
import random
import sys

import discord
import dotenv

dotenv.load_dotenv(".env")
token = os.getenv("DISCORD_TOKEN")
logfile = os.getenv("DISCORD_BOT_LOGFILE")


client = discord.Client()
logging.basicConfig(stream=sys.stderr, level=logging.INFO)

WINNERS = collections.defaultdict(int)
LOSERS = collections.defaultdict(int)


async def roll_die_and_update(message):
    text = message.content[2:]
    num = -1
    try:
        num = int(text)
    except Exception:
        logging.info(f"{message.content} looked like a dice roll but failed to parse")
        return
    roll = random.randint(1, num)
    if roll == 1:
        logging.info(f"{message.author.name} - critical failure")
        LOSERS[message.author.id] += 1
    elif roll == num:
        logging.info(f"{message.author.name} - critical success")
        WINNERS[message.author.id] += 1
    await message.channel.send(f"```# {roll}\nDetails: [d{num} ({roll})]```")


async def scoreboard_command(channel):
    msg = "**Winning rolls:**\n"
    for user_id, wins in sorted(WINNERS.items(), key=lambda kv: kv[1]):
        msg += f"<@{user_id}>: {wins}\n"
    msg += "\n**Losing rolls:**\n"
    for user_id, wins in sorted(LOSERS.items(), key=lambda kv: kv[1]):
        msg += f"<@{user_id}>: {wins}\n"
    await channel.send(msg)


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.content.startswith("!d"):
        last_user = message.author
        await roll_die_and_update(message)
    elif message.content.startswith("!scoreboard"):
        await scoreboard_command(message.channel)


print("Starting bot.")
client.run(token)
