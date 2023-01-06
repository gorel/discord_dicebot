#!/usr/bin/env python3

import asyncio
import unittest

from dicebot.commands import myrandom
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.test.utils import TestMessageContext


class TestMyRandom(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        asyncio.get_running_loop().set_debug(False)

    async def test_choice(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        # Act
        await myrandom.choice(ctx, GreedyStr("a b c"))
        # Assert
        ctx.quote_reply.assert_awaited_once()
