#!/usr/bin/env python3

import datetime
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

import discord

from dicebot.data.db.active_event import EventType
from dicebot.tasks.daily_event import check_daily_event_async
from dicebot.test.utils import DicebotTestCase


def _make_session_mock():
    mock_session = AsyncMock()
    mock_session.__aenter__ = AsyncMock(return_value=mock_session)
    mock_session.__aexit__ = AsyncMock(return_value=False)
    return mock_session


def _make_guild_mock(events_probability=0.25, events_channel_id=12345, timezone="US/Pacific", guild_id=1):
    mock_guild = MagicMock()
    mock_guild.events_probability = events_probability
    mock_guild.events_channel_id = events_channel_id
    mock_guild.timezone = timezone
    mock_guild.id = guild_id
    return mock_guild


class TestCheckDailyEventSkips(DicebotTestCase):
    @patch("dicebot.tasks.daily_event.Guild.get_all", new_callable=AsyncMock)
    @patch("dicebot.tasks.daily_event.Client.get_and_login", new_callable=AsyncMock)
    async def test_skips_guild_with_no_probability(self, mock_login, mock_get_all):
        """Guild with events_probability=None is skipped, no event created."""
        mock_client = AsyncMock()
        mock_login.return_value = mock_client

        mock_guild = _make_guild_mock(events_probability=None)
        mock_get_all.return_value = [mock_guild]

        with patch("dicebot.tasks.daily_event.app_sessionmaker") as mock_sm:
            mock_session = _make_session_mock()
            mock_sm.return_value = mock_session
            await check_daily_event_async()

        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_awaited()

    @patch("dicebot.tasks.daily_event.Guild.get_all", new_callable=AsyncMock)
    @patch("dicebot.tasks.daily_event.Client.get_and_login", new_callable=AsyncMock)
    async def test_skips_guild_with_no_channel(self, mock_login, mock_get_all):
        """Guild with events_channel_id=None is skipped, no event created."""
        mock_client = AsyncMock()
        mock_login.return_value = mock_client

        mock_guild = _make_guild_mock(events_probability=0.5, events_channel_id=None)
        mock_get_all.return_value = [mock_guild]

        with patch("dicebot.tasks.daily_event.app_sessionmaker") as mock_sm:
            mock_session = _make_session_mock()
            mock_sm.return_value = mock_session
            await check_daily_event_async()

        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_awaited()

    @patch("dicebot.tasks.daily_event.Guild.get_all", new_callable=AsyncMock)
    @patch("dicebot.tasks.daily_event.Client.get_and_login", new_callable=AsyncMock)
    async def test_skips_wrong_hour(self, mock_login, mock_get_all):
        """When the local time is not 5am, no event is created."""
        mock_client = AsyncMock()
        mock_login.return_value = mock_client

        mock_guild = _make_guild_mock()
        mock_get_all.return_value = [mock_guild]

        with patch("dicebot.tasks.daily_event.datetime") as mock_dt:
            mock_now = MagicMock()
            mock_now.hour = 12  # not 5am
            mock_dt.datetime.now.return_value = mock_now
            mock_dt.timedelta = datetime.timedelta

            with patch("dicebot.tasks.daily_event.app_sessionmaker") as mock_sm:
                mock_session = _make_session_mock()
                mock_sm.return_value = mock_session
                await check_daily_event_async()

        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_awaited()

    @patch("dicebot.tasks.daily_event.ActiveEvent.get_current", new_callable=AsyncMock)
    @patch("dicebot.tasks.daily_event.Guild.get_all", new_callable=AsyncMock)
    @patch("dicebot.tasks.daily_event.Client.get_and_login", new_callable=AsyncMock)
    async def test_skips_if_event_already_exists(self, mock_login, mock_get_all, mock_get_current):
        """If an active event already exists for the guild today, no new event is created."""
        mock_client = AsyncMock()
        mock_login.return_value = mock_client

        mock_guild = _make_guild_mock()
        mock_get_all.return_value = [mock_guild]
        mock_get_current.return_value = MagicMock()  # existing event

        with patch("dicebot.tasks.daily_event.datetime") as mock_dt:
            mock_now = MagicMock()
            mock_now.hour = 5
            mock_dt.datetime.now.return_value = mock_now
            mock_dt.timedelta = datetime.timedelta

            with patch("dicebot.tasks.daily_event.app_sessionmaker") as mock_sm:
                mock_session = _make_session_mock()
                mock_sm.return_value = mock_session
                await check_daily_event_async()

        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_awaited()

    @patch("dicebot.tasks.daily_event.random")
    @patch("dicebot.tasks.daily_event.ActiveEvent.get_current", new_callable=AsyncMock)
    @patch("dicebot.tasks.daily_event.Guild.get_all", new_callable=AsyncMock)
    @patch("dicebot.tasks.daily_event.Client.get_and_login", new_callable=AsyncMock)
    async def test_skips_on_failed_roll(self, mock_login, mock_get_all, mock_get_current, mock_random):
        """When random roll exceeds guild probability, no event is created."""
        mock_client = AsyncMock()
        mock_login.return_value = mock_client

        mock_guild = _make_guild_mock(events_probability=0.25)
        mock_get_all.return_value = [mock_guild]
        mock_get_current.return_value = None  # no existing event
        mock_random.random.return_value = 0.99  # 0.99 > 0.25, so roll fails

        with patch("dicebot.tasks.daily_event.datetime") as mock_dt:
            mock_now = MagicMock()
            mock_now.hour = 5
            mock_dt.datetime.now.return_value = mock_now
            mock_dt.timedelta = datetime.timedelta

            with patch("dicebot.tasks.daily_event.app_sessionmaker") as mock_sm:
                mock_session = _make_session_mock()
                mock_sm.return_value = mock_session
                await check_daily_event_async()

        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_awaited()


class TestCheckDailyEventCreates(DicebotTestCase):
    @patch("dicebot.tasks.daily_event.random")
    @patch("dicebot.tasks.daily_event.ActiveEvent.get_current", new_callable=AsyncMock)
    @patch("dicebot.tasks.daily_event.Guild.get_all", new_callable=AsyncMock)
    @patch("dicebot.tasks.daily_event.Client.get_and_login", new_callable=AsyncMock)
    async def test_creates_event_and_announces(self, mock_login, mock_get_all, mock_get_current, mock_random):
        """When all conditions pass, an ActiveEvent is created and channel.send is called."""
        mock_client = AsyncMock()
        mock_login.return_value = mock_client

        mock_channel = AsyncMock(spec=discord.TextChannel)
        mock_client.fetch_channel = AsyncMock(return_value=mock_channel)

        mock_guild = _make_guild_mock(events_probability=0.25, events_channel_id=12345)
        mock_get_all.return_value = [mock_guild]
        mock_get_current.return_value = None  # no existing event
        mock_random.random.return_value = 0.1  # 0.1 < 0.25 → fires
        mock_random.choice.return_value = EventType.DOUBLE_BAN

        with patch("dicebot.tasks.daily_event.datetime") as mock_dt:
            mock_now = MagicMock()
            mock_now.hour = 5
            mock_dt.datetime.now.return_value = mock_now
            mock_dt.datetime.utcnow.return_value = datetime.datetime(2026, 4, 16, 13, 0, 0)
            mock_dt.timedelta = datetime.timedelta

            with patch("dicebot.tasks.daily_event.app_sessionmaker") as mock_sm:
                mock_session = _make_session_mock()
                mock_sm.return_value = mock_session
                await check_daily_event_async()

        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()
        mock_channel.send.assert_awaited_once()
        # Verify an embed was passed
        call_kwargs = mock_channel.send.call_args[1]
        self.assertIn("embed", call_kwargs)


if __name__ == "__main__":
    unittest.main()
