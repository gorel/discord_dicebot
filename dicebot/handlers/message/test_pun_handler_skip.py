#!/usr/bin/env python3

from unittest.mock import AsyncMock, patch

from dicebot.handlers.message.pun_handler import PunHandler
from dicebot.test.utils import TestMessageContext, DicebotTestCase
from dicebot.data.types.state_keys import WAS_REPOST


class TestPunHandlerSkip(DicebotTestCase):
    async def test_should_handle_normal(self):
        ctx = TestMessageContext.get("This is a ||pun|| message")
        handler = PunHandler()
        # No state flag set => should handle
        self.assertTrue(await handler.should_handle(ctx))

    async def test_should_not_handle_after_repost(self):
        ctx = TestMessageContext.get("This is a ||pun|| message")
        handler = PunHandler()
        # Simulate repost flag
        ctx.state[WAS_REPOST] = True
        self.assertFalse(await handler.should_handle(ctx))