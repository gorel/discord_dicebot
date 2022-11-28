#!/usr/bin/env python3

import asyncio
import datetime

import discord

from commands import ban
from message_context import MessageContext
from models import DiscordUser, Time
from on_reaction_handlers.abstract_reaction_handler import \
    AbstractReactionHandler


class BanReactionHandler(AbstractReactionHandler):
    @property
    def reaction_name(self) -> str:
        return "ban"

    async def handle(
        self,
        reaction: discord.Reaction,
        user: discord.User,
        ctx: MessageContext,
    ) -> None:
        # Special feature for people trying to ban the bot itself
        if ctx.client.user.id == ctx.message.author.id:
            # TODO: If it reaches the ban threshold, unban *everyone* in this server
            my_name = ctx.client.user.name
            await reaction.message.channel.send(
                f"Who *dares* try to ban the mighty {my_name}?!"
            )
            await ban.ban(
                ctx,
                target=DiscordUser(user.id),
                timer=Time("1hr"),
                ban_as_bot=True,
            )
            # Exit early
            return

        # Check if the user was turbo banned
        elapsed = datetime.datetime.now() - reaction.message.created_at
        turbo_ban = elapsed.total_seconds() <= ctx.server_ctx.turbo_ban_timing_threshold

        if turbo_ban:
            await ban.turboban(
                ctx,
                reference_msg=reaction.message,
                target=DiscordUser(reaction.message.author.id),
            )
        else:
            await reaction.message.channel.send("Bro", reference=reaction.message)
            # Sleep 3 seconds to build suspense
            await asyncio.sleep(3)
            await ban.ban(
                ctx,
                target=DiscordUser(reaction.message.author.id),
                timer=Time("1hr"),
                ban_as_bot=True,
            )
