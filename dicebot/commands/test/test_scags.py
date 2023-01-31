#!/usr/bin/env python3

from dicebot.commands import scags
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestScags(DicebotTestCase):
    async def test_choice(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        # Act
        await scags.scags(ctx)
        # Assert
        ctx.quote_reply.assert_awaited_once()
