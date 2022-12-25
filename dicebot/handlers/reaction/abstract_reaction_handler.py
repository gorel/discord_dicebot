#!/usr/bin/env python3

import logging
from abc import ABC, abstractmethod

from dicebot.data.db.reacted_message import ReactedMessage
from dicebot.data.types.message_context import MessageContext


class AbstractReactionHandler(ABC):
    @property
    @abstractmethod
    def reaction_name(self) -> str:
        pass

    async def should_handle(
        self,
        ctx: MessageContext,
    ) -> bool:
        assert ctx.reaction is not None
        is_proper_emoji = (
            not isinstance(ctx.reaction.emoji, str)
            and ctx.reaction.emoji.name.lower() == self.reaction_name
            and ctx.reaction.emoji.id is not None
        )
        if not is_proper_emoji:
            return False
        # Unfortunately pyright can't deduce these two facts
        assert not isinstance(ctx.reaction.emoji, str)
        assert ctx.reaction.emoji.id is not None

        # pyright doesn't realize this can't be a string now
        assert not isinstance(ctx.reaction.emoji, str)

        # Check if this message has been reacted before
        previous_reaction_record = await ReactedMessage.get_by_msg_and_reaction_id(
            ctx.session, ctx.reaction.message.id, ctx.reaction.emoji.id
        )
        if previous_reaction_record is not None:
            logging.warning("New reaction on message but it was reacted before.")
            return False

        # Only handle if we've hit the reaction threshold
        return ctx.reaction.count == ctx.guild.reaction_threshold

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
            reaction_id=ctx.reaction.emoji.id,
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
