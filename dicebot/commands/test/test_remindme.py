#!/usr/bin/env python3

import json
from unittest.mock import AsyncMock, patch

from dicebot.commands import remindme
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestRemindMe(DicebotTestCase):
    @patch("dicebot.commands.remindme.send_reminder")
    @patch("dicebot.commands.remindme.AskOpenAI")
    async def test_remindme_relative_time(
        self, mock_askopenai_cls, mock_send_reminder
    ) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        ai_response = json.dumps(
            {
                "seconds_until": 300,
                "reminder_text": "check the oven",
                "time_description": "in 5 minutes",
            }
        )
        mock_askopenai_cls.return_value.ask = AsyncMock(return_value=ai_response)
        # Act
        await remindme.remindme(ctx, GreedyStr("to check the oven in 5 minutes"))
        # Assert
        ctx.channel.send.assert_awaited_once()
        mock_send_reminder.apply_async.assert_called_once_with(
            (ctx.channel.id, ctx.author_id, "check the oven"), countdown=300
        )

    @patch("dicebot.commands.remindme.send_reminder")
    @patch("dicebot.commands.remindme.AskOpenAI")
    async def test_remindme_no_time_detected(
        self, mock_askopenai_cls, mock_send_reminder
    ) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        ai_response = json.dumps(
            {
                "seconds_until": -1,
                "reminder_text": "",
                "time_description": "",
            }
        )
        mock_askopenai_cls.return_value.ask = AsyncMock(return_value=ai_response)
        # Act
        await remindme.remindme(ctx, GreedyStr("do something"))
        # Assert
        ctx.channel.send.assert_awaited_once()
        mock_send_reminder.apply_async.assert_not_called()

    @patch("dicebot.commands.remindme.send_reminder")
    @patch("dicebot.commands.remindme.AskOpenAI")
    async def test_remindme_invalid_json(
        self, mock_askopenai_cls, mock_send_reminder
    ) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        mock_askopenai_cls.return_value.ask = AsyncMock(return_value="not json at all")
        # Act
        await remindme.remindme(ctx, GreedyStr("to check the oven in 5 minutes"))
        # Assert
        ctx.channel.send.assert_awaited_once()
        mock_send_reminder.apply_async.assert_not_called()
