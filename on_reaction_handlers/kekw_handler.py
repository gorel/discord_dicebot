#!/usr/bin/env python3

import time

import discord

from commands import ban
from message_context import MessageContext
from models import DiscordUser
from on_reaction_handlers.abstract_reaction_handler import \
    AbstractReactionHandler


class KekwReactionHandler(AbstractReactionHandler):
    @property
    def reaction_name(self) -> str:
        return "kekw"

    async def handle(
        self,
        reaction: discord.Reaction,
        user: discord.User,
        ctx: MessageContext,
    ) -> None:
        # This is the easiest way to pull the same kekw emoji
        emojis = {e.name.lower(): f"<:{e.name}:{e.id}>" for e in ctx.client.emojis}
        await reaction.message.channel.send(
            emojis[reaction.emoji.name.lower()], reference=reaction.message
        )

        # If the user is banned, unban them early
        current_ban = ctx.server_ctx.bans.get(user.id, -1)
        if current_ban > time.time():
            await ctx.channel.send(
                "That's good stuff, I'm unbanning you early.",
                reference=reaction.message,
            )
            await ban.unban(ctx, DiscordUser(user.id))
