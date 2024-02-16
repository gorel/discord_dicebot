#!/usr/bin/env python3

from dicebot.commands import clear_stats
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestClearStats(DicebotTestCase):
    async def test_clear_stats(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        # Act
        await clear_stats.clear_stats(ctx)
        # Assert
        ctx.guild.clear_stats.assert_awaited_once_with(ctx.session)
        ctx.send.assert_awaited_once()
