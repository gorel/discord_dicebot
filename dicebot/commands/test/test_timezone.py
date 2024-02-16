#!/usr/bin/env python3

import datetime
from unittest.mock import MagicMock, patch

from dicebot.commands import timezone
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestTimezone(DicebotTestCase):
    def test_localize_pretty(self) -> None:
        # Arrange
        now_dt = datetime.datetime(
            year=2023, month=1, day=6, tzinfo=datetime.timezone.utc
        )
        past_tests = [
            (now_dt.replace(day=5, hour=23, minute=59, second=59), "1 second ago"),
            (now_dt.replace(day=5, hour=23, minute=59, second=50), "10 seconds ago"),
            (now_dt.replace(day=5, hour=23, minute=59), "1 minute ago"),
            (now_dt.replace(day=5, hour=23, minute=40), "20 minutes ago"),
            (now_dt.replace(day=5), "yesterday at 12:00 AM UTC"),
            (now_dt.replace(day=1), "last Sunday at 12:00 AM UTC"),
        ]
        future_tests = [
            (now_dt.replace(second=1), "1 second from now"),
            (now_dt.replace(second=10), "10 seconds from now"),
            (now_dt.replace(minute=1), "1 minute from now"),
            (now_dt.replace(minute=20), "20 minutes from now"),
            (now_dt.replace(day=7), "tomorrow at 12:00 AM UTC"),
            (now_dt.replace(hour=1), "1 hour from now"),
            (now_dt.replace(hour=3), "3 hours from now"),
            (now_dt.replace(day=12), "Thursday at 12:00 AM UTC"),
            (now_dt.replace(year=2025), "Jan 06, 2025 at 12:00 AM UTC"),
            (now_dt.replace(month=2, day=20), "Feb 20 at 12:00 AM UTC"),
        ]
        for target_dt, expected in past_tests + future_tests:
            # Act
            actual = timezone._localize_pretty(now_dt, target_dt)
            # Assert
            self.assertEqual(expected, actual)

    def test_localize(self) -> None:
        # Arrange
        unixtime = 1672981200
        expected_dt = datetime.datetime(year=2023, month=1, day=6)
        now_dt = expected_dt.replace(minute=30, tzinfo=datetime.timezone.utc)
        expected = "30 minutes ago"
        # Act
        with patch("dicebot.commands.timezone.datetime.datetime") as mock_dt:
            mock_dt.now = MagicMock(return_value=now_dt)
            mock_dt.utcfromtimestamp = MagicMock(return_value=expected_dt)
            actual = timezone.localize(unixtime, "UTC")
        # Assert
        self.assertEqual(expected, actual)

    def test_localize_dt(self) -> None:
        # Arrange
        target_dt = datetime.datetime(year=2023, month=1, day=6)
        now_dt = target_dt.replace(minute=30, tzinfo=datetime.timezone.utc)
        expected = "30 minutes ago"
        # Act
        with patch("dicebot.commands.timezone.datetime.datetime") as mock_dt:
            mock_dt.now = MagicMock(return_value=now_dt)
            mock_dt.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)
            mock_dt.now = MagicMock(return_value=now_dt)
            actual = timezone.localize_dt(target_dt, "UTC")
        # Assert
        self.assertEqual(expected, actual)

    async def test_set_tz(self) -> None:
        with self.subTest("valid timezone"):
            # Arrange
            ctx = TestMessageContext.get()
            tz = "US/Pacific"
            # Act
            await timezone.set_tz(ctx, tz)
            # Assert
            self.assertEqual(tz, ctx.guild.timezone)
            ctx.session.commit.assert_awaited_once()
            ctx.send.assert_awaited_once()
        with self.subTest("invalid timezone"):
            # Arrange
            ctx = TestMessageContext.get()
            tz = "Jupiter"
            # Act
            await timezone.set_tz(ctx, tz)
            # Assert
            ctx.send.assert_awaited_once()
