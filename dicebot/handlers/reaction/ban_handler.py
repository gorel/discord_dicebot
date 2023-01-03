#!/usr/bin/env python3

import asyncio
import datetime

from dicebot.commands import ban
from dicebot.data.db.user import User
from dicebot.data.types.message_context import MessageContext
from dicebot.data.types.time import Time
from dicebot.handlers.reaction.abstract_reaction_handler import AbstractReactionHandler


class BanReactionHandler(AbstractReactionHandler):
    @property
    def reaction_name(self) -> str:
        return "ban"

    async def should_handle(
        self,
        ctx: MessageContext,
    ) -> bool:
        if await self.should_handle_without_threshold_check(ctx):
            # Appease pyright
            assert ctx.reaction is not None
            assert not isinstance(ctx.reaction.emoji, str)
            assert ctx.client.user is not None
            assert ctx.reactor is not None

            # Special feature for people trying to ban the bot itself
            if ctx.client.user.id == ctx.message.author.id:
                my_name = ctx.client.user.name
                await ctx.reaction.message.channel.send(
                    f"Who *dares* try to ban the mighty {my_name}?!"
                )
                discord_user = await User.get_or_create(ctx.session, ctx.reactor.id)
                await ban.ban_internal(
                    ctx,
                    target=discord_user,
                    timer=Time("1hr"),
                    ban_as_bot=True,
                    reason="Tried to react-ban the bot",
                )

        return await super().should_handle(ctx)

    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        # Appease pyright
        assert ctx.reaction is not None
        assert ctx.reactor is not None
        assert ctx.client.user is not None

        # Special feature for people trying to ban the bot itself
        if ctx.client.user.id == ctx.message.author.id:
            msg = (
                f"What's this?! {ctx.reaction.count} bans against _me?_\n"
                "Perhaps I was too harsh on you all."
            )
            await ctx.reaction.message.channel.send(msg)
            await asyncio.sleep(1)
            async for user in ctx.reaction.users():
                discord_user = await User.get_or_create(ctx.session, user.id)
                await ban.unban_internal(
                    ctx, discord_user, f"<@{user.id}> has been unbanned early."
                )
            # Exit early
            return

        # Check if the user was turbo banned
        current_date = datetime.datetime.now()
        now = current_date.replace(tzinfo=datetime.timezone.utc)
        elapsed = now - ctx.reaction.message.created_at
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
            await ban.ban_internal(
                ctx,
                target=discord_user,
                timer=Time("1hr"),
                ban_as_bot=True,
                reason="Got react-banned",
            )
