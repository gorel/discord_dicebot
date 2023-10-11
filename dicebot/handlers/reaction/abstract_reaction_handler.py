#!/usr/bin/env python3

import logging
from abc import ABC, abstractmethod

from discord import Reaction

from dicebot.data.db.reacted_message import ReactedMessage
from dicebot.data.types.message_context import MessageContext


class AbstractReactionHandler(ABC):
    @property
    @abstractmethod
    def reaction_name(self) -> str:
        pass

    def is_emoji_with_name(self, reaction: Reaction, target_name: str) -> bool:
        return (
            not isinstance(reaction.emoji, str)
            and reaction.emoji.name.lower() == target_name
            and reaction.emoji.id is not None
        )

    def is_proper_emoji(self, reaction: Reaction) -> bool:
        return self.is_emoji_with_name(reaction, self.reaction_name)

    def get_emoji_id(self, reaction: Reaction) -> int:
        if isinstance(reaction.emoji, str):
            # We hack it to make it work for strings
            return ord(reaction.emoji[0])
        else:
            assert reaction.emoji.id is not None
            return reaction.emoji.id

    async def was_reacted_before(self, ctx: MessageContext) -> bool:
        """Check if this message has been reacted before"""

        assert ctx.reaction is not None

        previous_reaction_record = await ReactedMessage.get_by_msg_and_reaction_id(
            ctx.session, ctx.reaction.message.id, self.get_emoji_id(ctx.reaction)
        )
        return previous_reaction_record is not None

    async def should_handle_without_threshold_check(
        self,
        ctx: MessageContext,
    ) -> bool:
        assert ctx.reaction is not None
        if not self.is_proper_emoji(ctx.reaction):
            return False

        # Unfortunately pyright can't deduce these two facts
        assert not isinstance(ctx.reaction.emoji, str)
        assert ctx.reaction.emoji.id is not None

        # pyright doesn't realize this can't be a string now
        assert not isinstance(ctx.reaction.emoji, str)

        # Check if this message has been reacted before
        if await self.was_reacted_before(ctx):
            logging.warning("New reaction on message but it was reacted before.")
            return False

        return True

    def meets_threshold_check(self, ctx: MessageContext) -> bool:
        if ctx.reaction is None:
            return False

        # Only handle if we've hit the reaction threshold
        have = ctx.reaction.count
        want = ctx.guild.reaction_threshold
        logging.debug(f"Got reaction {ctx.reaction} ({have} / {want})")
        return ctx.reaction.count == ctx.guild.reaction_threshold

    async def should_handle(
        self,
        ctx: MessageContext,
    ) -> bool:
        basic_criteron = await self.should_handle_without_threshold_check(ctx)
        return basic_criteron and self.meets_threshold_check(ctx)

    @abstractmethod
    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        pass

    async def record_handled(
        self,
        ctx: MessageContext,
    ) -> None:
        assert ctx.reaction is not None
        assert not isinstance(ctx.reaction.emoji, str)
        assert ctx.reaction.emoji.id is not None

        reaction_record = ReactedMessage(
            guild_id=ctx.guild.id,
            msg_id=ctx.reaction.message.id,
            reaction_id=self.get_emoji_id(ctx.reaction),
        )
        ctx.session.add(reaction_record)
        await ctx.session.commit()

    async def handle_and_record_no_throw(
        self,
        ctx: MessageContext,
    ) -> None:
        try:
            if await self.should_handle(ctx):
                await self.handle(ctx)
                await self.record_handled(ctx)
        except Exception as e:
            logging.exception(
                "Exception raised in handle_and_record "
                f"for {self.__class__.__name__}: {e}"
            )
