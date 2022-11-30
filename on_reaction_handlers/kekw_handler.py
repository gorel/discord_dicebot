#!/usr/bin/env python3

import datetime

from commands import ban
from data_infra.db_models import Ban, DiscordUser
from data_infra.message_context import MessageContext
from on_reaction_handlers.abstract_reaction_handler import \
    AbstractReactionHandler


class KekwReactionHandler(AbstractReactionHandler):
    @property
    def reaction_name(self) -> str:
        return "kekw"

    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        assert not isinstance(ctx.reaction.emoji, str)
        # This is the easiest way to pull the same kekw emoji
        emojis = {e.name.lower(): f"<:{e.name}:{e.id}>" for e in ctx.client.emojis}
        await ctx.reaction.message.channel.send(
            emojis[ctx.reaction.emoji.name.lower()], reference=ctx.reaction.message
        )

        # If the user is banned, unban them early
        current_ban = Ban.get_latest_unvoided_ban(
            ctx.session, ctx.guild_id, ctx.reactor.id
        )
        if current_ban > datetime.datetime.now():
            await ctx.channel.send(
                "That's good stuff, I'm unbanning you early.",
                reference=ctx.reaction.message,
            )
            discord_user = await DiscordUser.get_or_create(ctx.reactor.id)
            await ban.unban(ctx, discord_user)
