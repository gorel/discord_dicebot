#!/usr/bin/env python3

import asyncio
import unittest

from dicebot.commands import clear_stats
from dicebot.test.utils import TestMessageContext


class TestClearStats(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        asyncio.get_running_loop().set_debug(False)

    async def test_clear_stats(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        # Act
        await clear_stats.clear_stats(ctx)
        # Assert
        ctx.guild.clear_stats.assert_awaited_once_with(ctx.session)
        ctx.channel.send.assert_awaited_once()
