#!/usr/bin/env python3

from dicebot.commands import myrandom
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestMyRandom(DicebotTestCase):
    async def test_choice(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        # Act
        await myrandom.choice(ctx, GreedyStr("a b c"))
        # Assert
        ctx.quote_reply.assert_awaited_once()
