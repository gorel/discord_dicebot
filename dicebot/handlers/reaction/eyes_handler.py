#!/usr/bin/env python3

import logging

from sqlalchemy.exc import IntegrityError

from dicebot.data.db.scheduled_event import ScheduledEvent, ScheduledEventSignup
from dicebot.data.types.message_context import MessageContext
from dicebot.handlers.reaction.abstract_reaction_handler import AbstractReactionHandler


class EyesReactionHandler(AbstractReactionHandler):
    @property
    def reaction_name(self) -> str:
        return "eyes"

    async def should_handle(self, ctx: MessageContext) -> bool:
        if ctx.reaction is None:
            return False
        if not self.is_emoji_with_name(ctx.reaction, self.reaction_name):
            return False
        assert ctx.reaction is not None
        # Only handle if this message corresponds to a scheduled event
        event = await ScheduledEvent.get_by_message_id(ctx.session, ctx.reaction.message.id)
        return event is not None

    async def handle(self, ctx: MessageContext) -> None:
        assert ctx.reaction is not None
        assert ctx.reactor is not None

        event = await ScheduledEvent.get_by_message_id(ctx.session, ctx.reaction.message.id)
        if event is None:
            return

        try:
            signup = ScheduledEventSignup(
                event_id=event.id,
                user_id=ctx.reactor.id,
            )
            ctx.session.add(signup)
            await ctx.session.commit()
        except IntegrityError:
            # Already signed up — unique constraint violation, silently ignore
            await ctx.session.rollback()

    async def record_handled(self, ctx: MessageContext) -> None:
        # EyesReactionHandler does not use ReactedMessage deduplication.
        # Duplicate signups are handled by the UniqueConstraint on ScheduledEventSignup.
        pass
