#!/usr/bin/env python3

"""
Discord bot used for rolling dice and other fun things

Usage:
    bot.py [options]

Options:
    -h --help   Show this help text
    -t --test   Set the bot to only respond to messages prepended with TEST
"""

import logging
import os
import pathlib
import sys

import discord
import docopt
import dotenv
import schema
import sqlite3

import db_helper
from server_manager import ServerManager


DEFAULT_DB_FILENAME = "discord_bot.sqlite"
DEFAULT_SERVER_MANAGER_FILENAME = "server_manager.pkl"


class Client(discord.Client):
    def __init__(
        self,
        db_conn: sqlite3.Connection,
        mgr_path: pathlib.Path,
        is_test: bool = False,
    ):
        super().__init__()
        self.db_conn = db_conn
        self.mgr_path = mgr_path
        self.is_test = is_test

    async def on_message(self, message) -> None:
        if message.author == self.user:
            # Don't let the bot respond to itself
            return

        # Test messages are designated with a leading "tt "
        if self.is_test:
            if message.content.startswith("tt "):
                message.content = message.content[len("tt ") :]
            else:
                return

        mgr = ServerManager.try_load(self.mgr_path)
        await mgr.handle(self, message, self.db_conn)
        mgr.save(self.mgr_path)


def main() -> None:
    # Load environment
    dotenv.load_dotenv(".env")
    db_filename = pathlib.Path(os.getenv("DB_FILENAME") or DEFAULT_DB_FILENAME)
    server_manager_filename = pathlib.Path(
        os.getenv("SERVER_MANAGER_FILENAME") or DEFAULT_SERVER_MANAGER_FILENAME
    )
    discord_token = os.getenv("DISCORD_TOKEN")

    # Validate cmdline args
    s = schema.Schema({"--help": bool, "--test": bool})
    args = s.validate(docopt.docopt(__doc__))

    # Set up stderr logging
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)

    # Ensure DB setup is complete
    logging.info("Setting up db connection and tables")
    conn = db_helper.db_connect(db_filename)
    db_helper.create_all(conn)

    # And start the client
    logging.info("Running client")
    client = Client(conn, server_manager_filename, is_test=args["--test"])
    client.run(discord_token)


if __name__ == "__main__":
    main()
