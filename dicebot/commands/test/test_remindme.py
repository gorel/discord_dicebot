#!/usr/bin/env python3

from unittest.mock import patch

from dicebot.commands import remindme
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.time import Time
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestRemindMe(DicebotTestCase):
    @patch("dicebot.commands.remindme.send_reminder")
    async def test_remindme(self, mock_send_reminder) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        # Act
        await remindme.remindme(ctx, Time("1hr"), GreedyStr("reminder"))
        # Assert
        ctx.send.assert_awaited_once()
        mock_send_reminder.apply_async.assert_called_once()
