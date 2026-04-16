#!/usr/bin/env python3

import discord
from unittest.mock import AsyncMock, MagicMock, patch

from dicebot.data.db.scheduled_event import ScheduledEvent, ScheduledEventSignup
from dicebot.tasks.notify_event import _notify_event_async
from dicebot.test.utils import DicebotTestCase


class TestNotifyEvent(DicebotTestCase):
    @patch("dicebot.core.client.Client.get_and_login", new_callable=AsyncMock)
    @patch("dicebot.data.db.scheduled_event.ScheduledEvent.get_by_id", new_callable=AsyncMock)
    @patch("dicebot.data.db.scheduled_event.ScheduledEventSignup.get_all_for_event", new_callable=AsyncMock)
    @patch("dicebot.tasks.notify_event.app_sessionmaker")
    async def test_notify_no_signups(self, mock_sm, mock_signups, mock_get_event, mock_login):
        mock_client = AsyncMock()
        mock_login.return_value = mock_client
        mock_channel = AsyncMock(spec=discord.TextChannel)
        mock_client.fetch_channel = AsyncMock(return_value=mock_channel)
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_sm.return_value = mock_session
        mock_event = MagicMock(spec=ScheduledEvent, name="Jackbox", id=1)
        mock_get_event.return_value = mock_event
        mock_signups.return_value = []

        await _notify_event_async(1, 100)

        mock_channel.send.assert_awaited_once()
        msg = mock_channel.send.call_args[0][0]
        assert "No one signed up" in msg

    @patch("dicebot.core.client.Client.get_and_login", new_callable=AsyncMock)
    @patch("dicebot.data.db.scheduled_event.ScheduledEvent.get_by_id", new_callable=AsyncMock)
    @patch("dicebot.data.db.scheduled_event.ScheduledEventSignup.get_all_for_event", new_callable=AsyncMock)
    @patch("dicebot.tasks.notify_event.app_sessionmaker")
    async def test_notify_with_signups(self, mock_sm, mock_signups, mock_get_event, mock_login):
        mock_client = AsyncMock()
        mock_login.return_value = mock_client
        mock_channel = AsyncMock(spec=discord.TextChannel)
        mock_client.fetch_channel = AsyncMock(return_value=mock_channel)
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_sm.return_value = mock_session
        mock_event = MagicMock(spec=ScheduledEvent, name="Jackbox", id=1)
        mock_get_event.return_value = mock_event
        signup = MagicMock(spec=ScheduledEventSignup, user_id=123)
        mock_signups.return_value = [signup]

        await _notify_event_async(1, 100)

        mock_channel.send.assert_awaited_once()
        msg = mock_channel.send.call_args[0][0]
        assert "<@123>" in msg
        assert "Jackbox" in msg

    @patch("dicebot.core.client.Client.get_and_login", new_callable=AsyncMock)
    @patch("dicebot.data.db.scheduled_event.ScheduledEvent.get_by_id", new_callable=AsyncMock)
    @patch("dicebot.tasks.notify_event.app_sessionmaker")
    async def test_notify_cancelled_event(self, mock_sm, mock_get_event, mock_login):
        mock_client = AsyncMock()
        mock_login.return_value = mock_client
        mock_channel = AsyncMock(spec=discord.TextChannel)
        mock_client.fetch_channel = AsyncMock(return_value=mock_channel)
        mock_session = AsyncMock()
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)
        mock_sm.return_value = mock_session
        mock_get_event.return_value = None  # Event was cancelled

        await _notify_event_async(1, 100)

        mock_channel.send.assert_not_awaited()
