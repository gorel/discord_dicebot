#!/usr/bin/env python3

import logging
from dicebot.commands.ask import AskOpenAI
from dicebot.data.types.message_context import MessageContext
from dicebot.data.types import state_keys
from dicebot.handlers.message.abstract_handler import AbstractHandler


class PunHandler(AbstractHandler):
    """Easter egg if the bot detects a pun in a message."""

    async def should_handle(
        self,
        ctx: MessageContext,
    ) -> bool:
        return "||" in ctx.message.content and ctx.message.guild is not None

    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        asker = AskOpenAI()
        resp = await asker.ask(
            "Does this look like a pun?\n"
            "Only answer yes or no, nothing else:\n"
            f"{ctx.message.content}"
        )
        if "yes" in resp.lower():
            ctx.state[state_keys.WAS_PUN] = True
            guild = ctx.message.guild
            # `should_handle` verified that this is a guild context
            assert guild is not None

            await ctx.quote_reply("Pun detected. Proactively banning user.")
            guild_emojis = {e.name.lower(): e for e in guild.emojis}
            all_emojis = {e.name.lower(): e for e in ctx.client.emojis}
            if "ban" in guild_emojis.keys():
                await ctx.message.add_reaction(guild_emojis["ban"])
            elif "ban" in all_emojis.keys():
                await ctx.message.add_reaction(all_emojis["ban"])
            else:
                logging.warning("No ban emoji found")
