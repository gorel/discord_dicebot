#!/usr/bin/env python3

import asyncio
import unittest
from unittest.mock import patch

from dicebot.commands import remindme
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.time import Time
from dicebot.test.utils import TestMessageContext


class TestRemindMe(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        asyncio.get_running_loop().set_debug(False)

    @patch("dicebot.commands.remindme.send_reminder")
    async def test_remindme(self, mock_send_reminder) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        # Act
        await remindme.remindme(ctx, Time("1hr"), GreedyStr("reminder"))
        # Assert
        ctx.channel.send.assert_awaited_once()
        mock_send_reminder.apply_async.assert_called_once()
