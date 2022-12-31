#!/usr/bin/env python3

import logging
import os
from typing import Optional

from dicebot.core.command_runner import CommandRunner
from dicebot.core.constants import DEFAULT_WEB_URL, WEB_URL_KEY
from dicebot.data.types.message_context import MessageContext
from dicebot.handlers.message.abstract_handler import AbstractHandler


class CommandHandler(AbstractHandler):
    """Default command runner"""

    def __init__(self) -> None:
        self.runner = CommandRunner()

    async def should_handle(
        self,
        ctx: MessageContext,
    ) -> bool:
        return ctx.message.content.startswith("!")

    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        # TODO: Help text is too long... need to make it shorter
        # Maybe even throw it online somewhere as a URL?
        if ctx.message.content.startswith("!help") or ctx.message.content.startswith(
            "!commands"
        ):
            if " " in ctx.message.content:
                func = ctx.message.content.split(" ")[1]
                text = self.helptext(func)
            else:
                text = self.helptext()
            await ctx.channel.send(text)
            # Early return - just send help text and quit
            return

        try:
            await self.runner.call(ctx)
        except Exception as e:
            end = len(ctx.message.content)
            if " " in ctx.message.content:
                end = ctx.message.content.index(" ")
            func = ctx.message.content[1:end]
            helptext = self.helptext(func)
            logging.exception(f"Failed to call command: {e}")
            await ctx.channel.send(helptext)

    def helptext(self, cmd: Optional[str] = None) -> str:
        if cmd is not None:
            # Looking for a specific kind of help
            if cmd in self.runner.cmds:
                cmd_text = self.runner.helptext(self.runner.cmds[cmd])
            else:
                cmd_text = f"Could not find command '{cmd}'"
            return cmd_text
        else:
            base_url = os.getenv(WEB_URL_KEY, DEFAULT_WEB_URL)
            help_url = f"{base_url}/help"
            return help_url
