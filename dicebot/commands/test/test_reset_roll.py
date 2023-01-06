#!/usr/bin/env python3

import asyncio
import unittest

from dicebot.commands import reset_roll
from dicebot.test.utils import TestMessageContext


class TestResetRoll(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        asyncio.get_running_loop().set_debug(False)

    async def test_reset_roll(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        # Act
        await reset_roll.reset_roll(ctx, 123)
        # Assert
        self.assertEqual(123, ctx.guild.current_roll)
        ctx.session.commit.assert_awaited_once()
        ctx.channel.send.assert_awaited_once()
