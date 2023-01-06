#!/usr/bin/env python3

import asyncio
import unittest

from dicebot.commands import web
from dicebot.test.utils import TestMessageContext


class TestWeb(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        asyncio.get_running_loop().set_debug(False)

    async def test_web(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        # Act
        await web.web(ctx)
        # Assert
        ctx.channel.send.assert_awaited_once()
