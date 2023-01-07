#!/usr/bin/env python3

from unittest.mock import MagicMock, patch

from dicebot.commands import time
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestTime(DicebotTestCase):
    @patch("dicebot.commands.time.datetime")
    async def test_time(self, mock_datetime) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        timestamp = "01:23 PM UTC"
        mock_datetime.datetime.now = MagicMock(
            return_value=MagicMock(strftime=MagicMock(return_value=timestamp))
        )
        # Act
        with patch("dicebot.commands.time.pytz"):
            await time.time(ctx)
        # Assert
        ctx.channel.send.assert_awaited_once()
        self.assertIn(timestamp, ctx.channel.send.await_args.args[0])
