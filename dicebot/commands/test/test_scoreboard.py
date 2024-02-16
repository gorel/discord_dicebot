#!/usr/bin/env python3

from dicebot.commands import scoreboard
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestScoreboard(DicebotTestCase):
    async def test_scoreboard(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        # Act
        await scoreboard.scoreboard(ctx)
        # Assert
        ctx.guild.roll_scoreboard_str.assert_awaited_once()
        ctx.send.assert_awaited_once()
