#!/usr/bin/env python3


from message_context import MessageContext
from on_message_handlers.abstract_handler import AbstractHandler

LONG_MESSAGE_CHAR_THRESHOLD = 700
LONG_MESSAGE_RESPONSE = "https://user-images.githubusercontent.com/2358378/199403413-b1f903f3-998e-481c-9172-8b323cf746f4.png"


class LongMessageHandler(AbstractHandler):
    """Send a funny response for long messages"""

    async def should_handle(
        self,
        ctx: MessageContext,
    ) -> bool:
        return len(ctx.message.content) > LONG_MESSAGE_CHAR_THRESHOLD

    async def handle(
        self,
        ctx: MessageContext,
    ) -> None:
        await ctx.channel.send(LONG_MESSAGE_RESPONSE)
