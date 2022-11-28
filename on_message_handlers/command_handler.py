#!/usr/bin/env python3

import logging
from typing import Optional

from command_runner import CommandRunner
from message_context import MessageContext
from on_message_handlers.abstract_handler import AbstractHandler


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
        if ctx.message.content.startswith("!help"):
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
            # Print help on *all* commands
            cmds = [
                # Each line should be relatively short
                self.runner.helptext(cmd, limit=120)
                for cmd in self.runner.cmds.values()
            ]
            cmd_text = "**Commands:**\n"
            for cmd in cmds:
                cmd_text += f"\t{cmd}\n"

        return cmd_text
