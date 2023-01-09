#!/usr/bin/env python3

from dicebot.commands import ban
from dicebot.data.db.user import User
from dicebot.data.types.message_context import MessageContext
from dicebot.handlers.reaction.abstract_reaction_handler import AbstractReactionHandler


class KekwReactionHandler(AbstractReactionHandler):
    @property
    def reaction_name(self) -> str:
        return "kekw"

    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        # Appease pyright
        assert ctx.reaction is not None
        assert ctx.reactor is not None
        assert not isinstance(ctx.reaction.emoji, str)

        # This is the easiest way to pull the same kekw emoji
        emojis = {e.name.lower(): f"<:{e.name}:{e.id}>" for e in ctx.client.emojis}
        await ctx.quote_reply(emojis[ctx.reaction.emoji.name.lower()])

        # If the user is banned, unban them early
        if await ctx.author.is_currently_banned(ctx.session, ctx.guild):
            await ctx.quote_reply("That's good stuff, I'm unbanning you early.")
            discord_user = await User.get_or_create(ctx.session, ctx.author_id)
            await ban.unban_internal(
                ctx, discord_user, f"<@{ctx.author_id}> has been unbanned early."
            )
