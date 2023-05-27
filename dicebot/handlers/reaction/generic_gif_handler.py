#!/usr/bin/env python3

from dicebot.commands import giffer
from dicebot.data.types.message_context import MessageContext
from dicebot.handlers.reaction.abstract_reaction_handler import AbstractReactionHandler


class GenericGifReactionHandler(AbstractReactionHandler):
    def __init__(self) -> None:
        self.triggers = {
            "biden_nice": "Thanks, Obama",
            "cool_dab": "Cool dab",
            "deletethis": "Delete this",
            "livelaughlove": "live laugh love",
            "ok_boomer": "OK boomer",
            "this_tbh": "This is true",
            "press_f": "Press F to pay respects",
            "question": "Bro what",
        }

    @property
    def reaction_name(self) -> str:
        # Not relevant with this handler
        return "_"

    async def should_handle(
        self,
        ctx: MessageContext,
    ) -> bool:
        if not self.meets_threshold_check(ctx):
            return False

        if await self.was_reacted_before(ctx):
            return False

        assert ctx.reaction is not None
        # First check this server's custom reactions
        handlers = await ctx.guild.get_all_reaction_handlers(ctx.session)
        for handler in handlers:
            if handler.reaction_equal(ctx.reaction):
                return True
        # Then check the defaults
        for reaction_name in self.triggers:
            if self.is_emoji_with_name(ctx.reaction, reaction_name):
                return True
        return False

    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        # Appease pyright
        assert ctx.reaction is not None
        assert ctx.reactor is not None
        assert not isinstance(ctx.reaction.emoji, str)

        # First check this server's custom reactions
        handlers = await ctx.guild.get_all_reaction_handlers(ctx.session)
        for handler in handlers:
            if handler.reaction_equal(ctx.reaction):
                gif_url = await giffer.get_random_gif_url(handler.gif_search)
                if gif_url is not None:
                    await ctx.quote_reply(gif_url)
                # Regardless of whether we sent a quote reply, return here
                # because otherwise we may get an IndexError below for a bad lookup.
                return

        # Then check the defaults
        q = self.triggers[ctx.reaction.emoji.name.lower()]
        gif_url = await giffer.get_random_gif_url(q)
        if gif_url is not None:
            await ctx.quote_reply(gif_url)
