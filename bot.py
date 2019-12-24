import collections
import enum
import logging
import os
import random
import sys

import discord
import dotenv

import db_helper

dotenv.load_dotenv(".env")
DB_FILENAME = os.getenv("DB_FILENAME")
LOGFILE = os.getenv("DISCORD_BOT_LOGFILE")
TOKEN = os.getenv("DISCORD_TOKEN")


CLIENT = discord.Client()
DB_CONN = db_helper.db_connect(DB_FILENAME)
logging.basicConfig(stream=sys.stderr, level=logging.INFO)


class Status(enum.Enum):
    NONE = 0
    LOSE = 1
    WIN = 2


class Rename(enum.Enum):
    SERVER = 0
    TEXT_CHAT = 1


async def roll_die_simple(channel, num):
    roll = random.randint(1, num)
    await channel.send(f"```# {roll}\nDetails: [d{num} ({roll})]```")
    return roll


async def roll_die_and_update(channel, username, discord_id, num):
    status = Status.NONE
    roll = await roll_die_simple(channel, num)
    if roll == 1:
        logging.info(f"{username} - critical failure")
        await channel.send(f"<@{discord_id}> gets to rename the chat channel!")
        status = Status.LOSE
    elif roll == num:
        logging.info(f"{username} - critical success")
        await channel.send(f"<@{discord_id}> gets to rename the server!")
        status = Status.WIN
    return status


async def scoreboard_command(channel, winners, losers):
    msg = "**Winning rolls:**\n"
    for record in winners:
        msg += f"<@{record['discord_id']}>: {record['count']}"
    msg += "\n**Losing rolls:**\n"
    for record in losers:
        msg += f"<@{record['discord_id']}>: {record['count']}"
    await channel.send(msg)


async def rename_command(guild, channel, content, rename_loc):
    len_prefix = len("!rename ")
    new_name = content[len_prefix:]
    if rename_loc == Rename.SERVER:
        await channel.send(f"Setting server name to: {new_name}")
        await guild.edit(name=new_name, reason="Dice roll")
    elif rename_loc == Rename.TEXT_CHAT:
        await channel.send(f"Setting chat name to: {new_name}")
        await channel.edit(name=new_name, reason="Dice roll")


def log_message(guild_id, discord_id, username, content):
    logging.info(f"Guild ({guild_id}) {username} (id={discord_id}): {content}")


@CLIENT.event
async def on_message(message):
    if message.author == CLIENT.user:
        return

    guild = message.channel.guild
    channel = message.channel
    content = message.content
    guild_id = message.channel.guild.id
    discord_id = message.author.id
    username = message.author.name
    log_message(guild_id, discord_id, username, content)

    if content == "!roll":
        next_roll = db_helper.get_next_roll(DB_CONN, guild_id)
        logging.info(f"Next roll in guild ({guild_id}) for user {username} is {next_roll}")
        status = await roll_die_and_update(channel, username, discord_id, next_roll)

        if status == Status.LOSE:
            db_helper.add_loser(DB_CONN, guild_id, discord_id, next_roll)
        elif status == Status.WIN:
            db_helper.add_winner(DB_CONN, guild_id, discord_id, next_roll)
    elif content == "!scoreboard":
        logging.info(f"Request for scoreboard in guild ({guild_id})")
        winners = db_helper.get_all_winners(DB_CONN, guild_id)
        losers = db_helper.get_all_losers(DB_CONN, guild_id)
        await scoreboard_command(channel, winners, losers)
    elif content.startswith("!rename"):
        logging.info(f"{username} attempting to rename in guild ({guild_id})")
        rename_allowed = False

        # Check if this user was the last winner
        record = db_helper.get_last_winner(DB_CONN, guild_id)
        if record["discord_id"] == discord_id and record["rename_used"] == 0:
            rename_allowed = True
            await rename_command(guild, channel, content, Rename.SERVER)
            db_helper.record_rename_used_winner(
                DB_CONN, guild_id, discord_id, record["roll"]
            )

        # Check if this user was the last loser
        record = db_helper.get_last_loser(DB_CONN, guild_id)
        if record["discord_id"] == discord_id and record["rename_used"] == 0:
            rename_allowed = True
            await rename_command(guild, channel, content, Rename.TEXT_CHAT)
            db_helper.record_rename_used_loser(
                DB_CONN, guild_id, discord_id, record["roll"]
            )
        if not rename_allowed:
            msg = (f"I can't let you do that, <@{discord_id}>.\n"
                    "This incident will be recorded.")
            # TODO: React with skull or something
            await channel.send(msg)
    elif content.startswith("!d"):
        len_prefix = len("!d")
        try:
            num = int(content[len_prefix:])
            await roll_die_simple(channel, num)
        except Exception:
            await channel.send(f"Not sure what you want me to do with {content}.")


print("Creating db tables...", end="", flush=True)
db_helper.create_all(DB_CONN)
print("Done.")
print("Starting bot.")
CLIENT.run(TOKEN)
