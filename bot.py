import collections
import enum
import logging
import os
import pickle
import random
import sys

import discord
import dotenv

import db_helper


DEFAULT_ROLL_VALUE = 6
DICEBOSS_ROLENAME = "diceboss"


dotenv.load_dotenv(".env")
DB_FILENAME = os.getenv("DB_FILENAME")
ROLL_FILENAME = os.getenv("ROLL_FILENAME")
LOGFILE = os.getenv("DISCORD_BOT_LOGFILE")
TOKEN = os.getenv("DISCORD_TOKEN")
TEST_ENV = os.getenv("TEST_ENV")


CLIENT = discord.Client()
DB_CONN = db_helper.db_connect(DB_FILENAME)
logging.basicConfig(stream=sys.stderr, level=logging.INFO)


class Rename(enum.Enum):
    SERVER = 0
    TEXT_CHAT = 1


def get_roll_dict():
    d = {}
    try:
        with open(ROLL_FILENAME, "rb") as f:
            d = pickle.load(f)
    except Exception:
        logging.error(f"Failed to load roll file ({ROLL_FILENAME})")
    return d


def get_next_roll(roll_dict, guild_id):
    return roll_dict.get(guild_id, DEFAULT_ROLL_VALUE)


def set_roll_for_guild(roll_dict, guild_id, value):
    # Increment next roll value for this guild
    roll_dict[guild_id] = value
    with open(ROLL_FILENAME, "wb") as f:
        try:
            pickle.dump(roll_dict, f)
        except Exception:
            logging.error(f"Failed to write roll file ({ROLL_FILENAME})")


def has_diceboss_role(user):
    return any(role.name == DICEBOSS_ROLENAME for role in user.roles)


async def roll_die_simple(channel, num):
    roll = random.randint(1, num)
    await channel.send(f"```# {roll}\nDetails: [d{num} ({roll})]```")
    return roll


async def roll_die_and_update(channel, username, discord_id, num):
    roll = await roll_die_simple(channel, num)
    if roll == 1:
        logging.info(f"{username} - critical failure")
        await channel.send(f"<@{discord_id}> gets to rename the chat channel!")
    elif roll == num:
        logging.info(f"{username} - critical success")
        await channel.send(f"<@{discord_id}> gets to rename the server!")
    return roll


async def scoreboard_command(channel, stats):
    sorted_stats = sorted(stats, key=lambda record: record["wins"] - record["losses"])
    msg = "**Stats:**\n"
    for record in sorted_stats:
        user = CLIENT.get_user(record["discord_id"])
        if not user:
            user = await CLIENT.fetch_user(record["discord_id"])
        msg += f"\t- {user.name}: {record['wins']} wins, {record['losses']} losses ({record['attempts']} rolls)\n"
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

    # If we're in a test environment, only process commands starting with
    # "TEST " to not conflict with prod bot.
    if TEST_ENV:
        if not content.startswith("TEST "):
            return
        content = content[len("TEST ") :]

    if content == "!help":
        msg = "Bot usage:\n"
        msg += "\t- !roll: Roll the dice\n"
        msg += "\t- !scoreboard: Display the scoreboard\n"
        msg += "\t- !rename <name>: Rename the server/channel to <name>\n"
        msg += "\t- !resetroll <n>: Set next roll for server to <n>\n"
        msg += "\t- !clearstats: Clear all roll stats \\*CANNOT BE UNDONE\\*\n"
        msg += "\t- !info: Display current roll\n"
        msg += "\t- !code: Display the github address for the bot code\n"
        msg += "\t- !d<n>: Roll a die with N sides (doesn't record stats)\n"
        msg += "\t- !help: Display this help text again\n"
        await channel.send(msg)
    elif content == "!roll":
        roll_dict = get_roll_dict()
        next_roll = get_next_roll(roll_dict, guild_id)
        logging.info(
            f"Next roll in guild ({guild_id}) for user {username} is {next_roll}"
        )
        roll = await roll_die_and_update(channel, username, discord_id, next_roll)
        db_helper.record_roll(DB_CONN, guild_id, discord_id, roll, next_roll)

        if roll == next_roll:
            # Increment next roll value for this guild
            set_roll_for_guild(roll_dict, guild_id, next_roll + 1)
            logging.info(f"Set next roll for guild ({guild_id}) to {next_roll + 1}")
    elif content == "!scoreboard":
        logging.info(f"Request for scoreboard in guild ({guild_id})")
        stats = db_helper.get_all_stats(DB_CONN, guild_id)
        await scoreboard_command(channel, stats)
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
            msg = (
                f"I can't let you do that, <@{discord_id}>.\n"
                "This incident will be recorded."
            )
            # TODO: React with skull or something
            await channel.send(msg)
    elif content.startswith("!resetroll"):
        len_prefix = len("!resetroll")
        num_str = content[len_prefix:]
        try:
            num = int(num_str)
            roll_dict = get_roll_dict()
            set_roll_for_guild(roll_dict, guild_id, num)
            await channel.send(f"Set next roll for this server to {num}")
        except Exception:
            await channel.send(f"Not sure how to reset roll to {num_str}")
    elif content.startswith("!clearstats"):
        if has_diceboss_role(message.author):
            db_helper.clear_all(DB_CONN, guild_id)
            roll_dict = get_roll_dict()
            set_roll_for_guild(roll_dict, guild_id, DEFAULT_ROLL_VALUE)
            await channel.send(
                "All winner/loser stats have been cleared for this server."
            )
            await channel.send(
                f"The next roll for this server has been reset to {DEFAULT_ROLL_VALUE}."
            )
        else:
            await channel.send("You're not a diceboss.")
            await channel.send("Don't try that shit again, bucko.")
    elif content.startswith("!info"):
        roll_dict = get_roll_dict()
        next_roll = get_next_roll(roll_dict, guild_id)
        await channel.send(f"Current roll is {next_roll}.")
    elif content.startswith("!code"):
        await channel.send("https://github.com/gorel/discord_dicebot\n")
    elif content.startswith("!d") and len(content) > 2 and content[2].isdigit():
        len_prefix = len("!d")
        try:
            num = int(content[len_prefix:])
            roll_dict = get_roll_dict()
            await roll_die_simple(channel, num)
        except Exception:
            await channel.send(f"Not sure what you want me to do with {content}.")


print("Creating db tables...", end="", flush=True)
db_helper.create_all(DB_CONN)
print("Done.")
print("Starting bot.")
if TEST_ENV:
    print("Starting in TEST mode")
CLIENT.run(TOKEN)
