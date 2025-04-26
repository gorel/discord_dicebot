#!/usr/bin/env python3

import re

from dicebot.commands.ask import AskOpenAI
from dicebot.commands.ban import ban_internal
from dicebot.data.types.time import Time
from dicebot.data.types.message_context import MessageContext
from dicebot.data.types.state_keys import WAS_REPOST
from dicebot.data.db.pun import Pun
from dicebot.handlers.message.abstract_handler import AbstractHandler

# Regex to find the first text enclosed in spoilers
SPOILER_REGEX = re.compile(r"\|\|(.+?)\|\|", re.DOTALL)

class RepostHandler(AbstractHandler):
    """Detect reposted puns by comparing setups and ban repeat offenders."""

    async def should_handle(self, ctx: MessageContext) -> bool:
        content = ctx.message.content
        return bool(content and ctx.message.guild is not None and "||" in content)

    async def handle(self, ctx: MessageContext) -> None:
        content = ctx.message.content
        parts = content.split("||", 2)
        if len(parts) < 3:
            return
        setup = parts[0].strip()
        punchline = parts[1].strip()

        existing = await Pun.get_by_punchline(ctx.session, ctx.guild_id, punchline)
        if existing is None:
            # First occurrence: record setup & punchline
            await Pun.add_or_get(ctx.session, ctx.guild_id, setup, punchline, ctx.author_id)
            return

        # Compare stored setup vs new setup via OpenAI
        asker = AskOpenAI()
        prompt = (
            "Do these two pun setups look like the same joke? "
            "Only answer yes or no, nothing else:\n"
            f"Setup A: {existing.setup}\n"
            f"Setup B: {setup}"
        )
        resp = await asker.ask(prompt)
        if "yes" in resp.lower():
            # Notify and ban
            user = await ctx.client.fetch_user(existing.first_poster_id)
            await ctx.quote_reply(f"Looks like a repost from {user.name}")
            # Mark that a repost was handled to skip further pun logic
            ctx.state[WAS_REPOST] = True
            reason = f"Reposted a pun originally by {user.name}"
            await ban_internal(
                ctx,
                ctx.author,
                Time("1d"),
                ban_as_bot=True,
                reason=reason,
            )