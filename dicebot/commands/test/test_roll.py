#!/usr/bin/env python3

import asyncio
import unittest

from dicebot.commands import roll
from dicebot.test.utils import TestMessageContext


class TestRoll(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        asyncio.get_running_loop().set_debug(False)

    async def test_roll(self) -> None:
        # This method is complicated, I'll test it later.
        pass

    async def test_set_gambling_limit(self) -> None:
        with self.subTest("simple"):
            # Arrange
            ctx = TestMessageContext.get()
            # Act
            await roll.set_gambling_limit(ctx, 123)
            # Assert
            self.assertEqual(123, ctx.guild.gambling_limit)
            ctx.session.commit.assert_awaited_once()
            ctx.channel.send.assert_awaited_once()
        with self.subTest("negative"):
            # Arrange
            ctx = TestMessageContext.get()
            # Act
            await roll.set_gambling_limit(ctx, -1)
            # Assert
            self.assertIsNone(ctx.guild.gambling_limit)
            ctx.session.commit.assert_awaited_once()
            ctx.channel.send.assert_awaited_once()
