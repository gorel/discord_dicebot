#!/usr/bin/env python3

from dicebot.handlers.message.pun_handler import PunHandler
from dicebot.test.utils import TestMessageContext, DicebotTestCase


class TestPunHandlerSkip(DicebotTestCase):
    async def test_should_handle_normal(self):
        ctx = TestMessageContext.get("This is a ||pun|| message")
        handler = PunHandler()
        # No state flag set => should handle
        self.assertTrue(await handler.should_handle(ctx))
