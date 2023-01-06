#!/usr/bin/env python3

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from dicebot.commands import eight_ball
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.test.utils import TestMessageContext


class TestEightBall(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        asyncio.get_running_loop().set_debug(False)

    @patch("dicebot.commands.eight_ball.random")
    @patch("dicebot.commands.eight_ball.asyncio", sleep=AsyncMock())
    @patch("dicebot.commands.eight_ball.ban", ban_internal=AsyncMock())
    async def test_eight_ball(self, mock_ban, mock_asyncio, mock_random) -> None:
        with self.subTest("normal"):
            # Arrange
            mock_random.random = MagicMock(return_value=1)
            mock_random.choice = MagicMock(return_value="choice")
            ctx = TestMessageContext.get()
            # Act
            await eight_ball.eight_ball(ctx, GreedyStr("q?"))
            # Assert
            ctx.quote_reply.assert_awaited_once_with("choice")
        with self.subTest("banned"):
            # Arrange
            mock_random.random = MagicMock(return_value=0)
            ctx = TestMessageContext.get()
            # Act
            await eight_ball.eight_ball(ctx, GreedyStr("q?"))
            # Assert
            ctx.quote_reply.assert_awaited_once()
            mock_asyncio.sleep.assert_awaited_once()
            mock_ban.ban_internal.assert_awaited_once()
