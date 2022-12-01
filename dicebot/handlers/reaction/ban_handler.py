#!/usr/bin/env python3

import asyncio
import datetime

from dicebot.commands import ban
from dicebot.data.db.user import User
from dicebot.data.message_context import MessageContext
from dicebot.data.types.bot_param import BotParam
from dicebot.data.types.time import Time
from dicebot.handlers.reaction.abstract_reaction_handler import \
    AbstractReactionHandler


class BanReactionHandler(AbstractReactionHandler):
    @property
    def reaction_name(self) -> str:
        return "ban"

    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        # Appease pyright
        assert ctx.reaction is not None
        assert ctx.reactor is not None
        assert not isinstance(ctx.reaction.emoji, str)

        # Special feature for people trying to ban the bot itself
        if ctx.client.user.id == ctx.message.author.id:
            # TODO: If it reaches the ban threshold, unban *everyone* in this guild
            my_name = ctx.client.user.name
            await ctx.reaction.message.channel.send(
                f"Who *dares* try to ban the mighty {my_name}?!"
            )
            discord_user = await User.get_or_create(ctx.session, ctx.reactor.id)
            await ban.ban(
                ctx,
                target=discord_user,
                timer=Time("1hr"),
                ban_as_bot=BotParam(True),
            )
            # Exit early
            return

        # Check if the user was turbo banned
        elapsed = datetime.datetime.now() - ctx.reaction.message.created_at
        turbo_ban = elapsed.total_seconds() <= ctx.guild.turboban_threshold

        discord_user = await User.get_or_create(
            ctx.session, ctx.reaction.message.author.id
        )
        if turbo_ban:
            await ban.turboban(
                ctx,
                reference_msg=ctx.reaction.message,
                target=discord_user,
            )
        else:
            await ctx.reaction.message.channel.send(
                "Bro", reference=ctx.reaction.message
            )
            # Sleep 3 seconds to build suspense
            await asyncio.sleep(3)
            await ban.ban(
                ctx,
                target=discord_user,
                timer=Time("1hr"),
                ban_as_bot=BotParam(True),
            )
