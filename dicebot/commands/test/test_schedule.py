#!/usr/bin/env python3

import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from dicebot.commands import schedule
from dicebot.data.db.scheduled_event import ScheduledEvent, ScheduledEventSignup
from dicebot.test.utils import DicebotTestCase, TestMessageContext


def _make_typing_ctx_manager():
    """Return an async context manager mock suitable for channel.typing()."""
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=None)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm


class TestSchedule(DicebotTestCase):
    @patch("dicebot.commands.schedule.AskOpenAI")
    async def test_schedule_parse_failure(self, mock_ask_cls):
        # Arrange
        ctx = TestMessageContext.get()
        ctx.guild.timezone = "US/Pacific"
        ctx.channel.typing = MagicMock(return_value=_make_typing_ctx_manager())
        mock_asker = AsyncMock()
        mock_asker.ask = AsyncMock(return_value="not json")
        mock_ask_cls.return_value = mock_asker
        # Act
        await schedule.schedule(ctx, schedule.GreedyStr("play jackbox"))
        # Assert - error message sent, no session.add
        ctx.channel.send.assert_awaited()
        ctx.session.add.assert_not_called()

    @patch("dicebot.tasks.notify_event.notify_event")
    @patch("dicebot.commands.schedule.AskOpenAI")
    async def test_schedule_success(self, mock_ask_cls, mock_notify):
        # Arrange
        ctx = TestMessageContext.get()
        ctx.guild.timezone = "US/Pacific"
        ctx.channel.id = 42
        ctx.channel.typing = MagicMock(return_value=_make_typing_ctx_manager())
        mock_asker = AsyncMock()
        mock_asker.ask = AsyncMock(return_value='{"seconds_until": 3600, "event_name": "Jackbox", "time_description": "in 1 hour"}')
        mock_ask_cls.return_value = mock_asker
        mock_msg = MagicMock()
        mock_msg.id = 12345
        ctx.channel.send = AsyncMock(return_value=mock_msg)
        # Act
        await schedule.schedule(ctx, schedule.GreedyStr("jackbox in 1 hour"))
        # Assert
        ctx.session.add.assert_called_once()
        ctx.session.commit.assert_awaited()
        mock_notify.apply_async.assert_called_once()
        call_args = mock_notify.apply_async.call_args
        assert call_args.kwargs["countdown"] == 3600
        added_event = ctx.session.add.call_args[0][0]
        self.assertEqual(added_event.message_id, mock_msg.id)

    @patch("dicebot.commands.schedule.ScheduledEventSignup.get_all_for_event", new_callable=AsyncMock)
    @patch("dicebot.commands.schedule.ScheduledEvent.get_by_id", new_callable=AsyncMock)
    async def test_cancel_event_not_found(self, mock_get, mock_signups):
        # Arrange
        ctx = TestMessageContext.get()
        ctx.author.is_admin_of.return_value = True
        mock_get.return_value = None
        # Act
        await schedule.cancel_event(ctx, 99)
        # Assert
        ctx.channel.send.assert_awaited_once()
        ctx.session.delete.assert_not_called()

    @patch("dicebot.commands.schedule.ScheduledEvent.get_upcoming", new_callable=AsyncMock)
    async def test_list_events_no_events(self, mock_get_upcoming):
        # Arrange
        ctx = TestMessageContext.get()
        mock_get_upcoming.return_value = []
        # Act
        await schedule.list_events(ctx)
        # Assert
        ctx.channel.send.assert_awaited_once()
        call_kwargs = ctx.channel.send.call_args.kwargs
        embed = call_kwargs["embed"]
        self.assertEqual(embed.title, "Upcoming Events")
        self.assertEqual(len(embed.fields), 1)
        self.assertIn("No upcoming events", embed.fields[0].value)

    @patch("dicebot.commands.schedule.ScheduledEvent.get_upcoming", new_callable=AsyncMock)
    async def test_list_events_one_event(self, mock_get_upcoming):
        # Arrange
        ctx = TestMessageContext.get()
        ctx.guild.timezone = "US/Pacific"
        mock_event = MagicMock(spec=ScheduledEvent)
        mock_event.name = "Jackbox"
        mock_event.event_time = datetime.datetime(2099, 5, 1, 17, 0, 0)
        mock_get_upcoming.return_value = [mock_event]
        # Act
        await schedule.list_events(ctx)
        # Assert
        ctx.channel.send.assert_awaited_once()
        call_kwargs = ctx.channel.send.call_args.kwargs
        embed = call_kwargs["embed"]
        self.assertEqual(embed.title, "Upcoming Events")
        self.assertEqual(len(embed.fields), 1)
        self.assertEqual(embed.fields[0].name, "Jackbox")

    @patch("dicebot.commands.schedule.ScheduledEvent.get_upcoming", new_callable=AsyncMock)
    async def test_list_events_multiple_events(self, mock_get_upcoming):
        # Arrange
        ctx = TestMessageContext.get()
        ctx.guild.timezone = "US/Pacific"
        event1 = MagicMock(spec=ScheduledEvent)
        event1.name = "Jackbox"
        event1.event_time = datetime.datetime(2099, 5, 1, 17, 0, 0)
        event2 = MagicMock(spec=ScheduledEvent)
        event2.name = "Movie Night"
        event2.event_time = datetime.datetime(2099, 5, 8, 20, 0, 0)
        mock_get_upcoming.return_value = [event1, event2]
        # Act
        await schedule.list_events(ctx)
        # Assert
        ctx.channel.send.assert_awaited_once()
        call_kwargs = ctx.channel.send.call_args.kwargs
        embed = call_kwargs["embed"]
        self.assertEqual(len(embed.fields), 2)
        self.assertEqual(embed.fields[0].name, "Jackbox")
        self.assertEqual(embed.fields[1].name, "Movie Night")

    @patch("dicebot.commands.schedule.ScheduledEventSignup.get_all_for_event", new_callable=AsyncMock)
    @patch("dicebot.commands.schedule.ScheduledEvent.get_by_id", new_callable=AsyncMock)
    async def test_cancel_event_found(self, mock_get, mock_signups):
        # Arrange
        ctx = TestMessageContext.get()
        ctx.author.is_admin_of.return_value = True
        mock_event = MagicMock(spec=ScheduledEvent)
        mock_event.id = 1
        mock_event.name = "Jackbox"
        mock_get.return_value = mock_event
        mock_signups.return_value = []
        # Act
        await schedule.cancel_event(ctx, 1)
        # Assert
        ctx.session.delete.assert_called_once_with(mock_event)
        ctx.session.commit.assert_awaited_once()
        ctx.channel.send.assert_awaited_once()
