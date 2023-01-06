#!/usr/bin/env python3

import asyncio
import unittest

from dicebot.commands import scoreboard
from dicebot.test.utils import TestMessageContext


class TestScoreboard(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        asyncio.get_running_loop().set_debug(False)

    async def test_scoreboard(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        # Act
        await scoreboard.scoreboard(ctx)
        # Assert
        ctx.guild.roll_scoreboard_str.assert_awaited_once()
        ctx.channel.send.assert_awaited_once()
