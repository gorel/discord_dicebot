#!/usr/bin/env python3

import datetime
from unittest.mock import AsyncMock, MagicMock, create_autospec, patch

import discord

from dicebot.commands import stats
from dicebot.data.db.user import User
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestStats(DicebotTestCase):
    @patch("dicebot.commands.stats.get_roll_stats", autospec=True)
    @patch("dicebot.commands.stats.get_ban_stats", autospec=True)
    @patch("dicebot.commands.stats.get_social_stats", autospec=True)
    async def test_stats_defaults_to_author(
        self, mock_social, mock_ban, mock_roll
    ) -> None:
        """!stats with no arg shows stats for the invoking user"""
        # Arrange
        ctx = TestMessageContext.get()
        mock_roll.return_value = {"total": 0, "wins": 0, "losses": 0, "win_rate": "0%", "best": 0, "last_roll": "Never"}
        mock_ban.return_value = {"times_banned": 0, "currently_banned": "No", "immune": "No"}
        mock_social.return_value = {"thanks_given": 0, "thanks_received": 0, "puns_caught": 0}
        # Act
        await stats.stats(ctx, target=None)
        # Assert
        mock_roll.assert_awaited_once_with(ctx.session, ctx.guild, ctx.author)
        mock_ban.assert_awaited_once_with(ctx.session, ctx.guild, ctx.author)
        mock_social.assert_awaited_once_with(ctx.session, ctx.guild, ctx.author)
        ctx.channel.send.assert_awaited_once()
        # The embed should have been passed
        call_kwargs = ctx.channel.send.call_args.kwargs
        assert "embed" in call_kwargs

    @patch("dicebot.commands.stats.get_roll_stats", autospec=True)
    @patch("dicebot.commands.stats.get_ban_stats", autospec=True)
    @patch("dicebot.commands.stats.get_social_stats", autospec=True)
    async def test_stats_for_another_user(
        self, mock_social, mock_ban, mock_roll
    ) -> None:
        """!stats @someone shows stats for that user"""
        # Arrange
        ctx = TestMessageContext.get()
        other_user = create_autospec(User)
        other_user.id = 99999
        mock_roll.return_value = {"total": 10, "wins": 7, "losses": 3, "win_rate": "70%", "best": 95, "last_roll": "Apr 12, 2026"}
        mock_ban.return_value = {"times_banned": 2, "currently_banned": "No", "immune": "No"}
        mock_social.return_value = {"thanks_given": 3, "thanks_received": 5, "puns_caught": 1}
        # Act
        await stats.stats(ctx, target=other_user)
        # Assert
        mock_roll.assert_awaited_once_with(ctx.session, ctx.guild, other_user)
        mock_ban.assert_awaited_once_with(ctx.session, ctx.guild, other_user)
        mock_social.assert_awaited_once_with(ctx.session, ctx.guild, other_user)
        ctx.channel.send.assert_awaited_once()

    @patch("dicebot.commands.stats.get_roll_stats", autospec=True)
    @patch("dicebot.commands.stats.get_ban_stats", autospec=True)
    @patch("dicebot.commands.stats.get_social_stats", autospec=True)
    async def test_stats_embed_is_red_when_banned(
        self, mock_social, mock_ban, mock_roll
    ) -> None:
        """Embed color is red when the user is currently banned"""
        # Arrange
        ctx = TestMessageContext.get()
        mock_roll.return_value = {"total": 5, "wins": 2, "losses": 3, "win_rate": "40%", "best": 60, "last_roll": "Apr 10, 2026"}
        mock_ban.return_value = {"times_banned": 3, "currently_banned": "Yes (until Apr 15, 2026 12:00 PM UTC)", "immune": "No"}
        mock_social.return_value = {"thanks_given": 1, "thanks_received": 1, "puns_caught": 0}
        # Act
        await stats.stats(ctx, target=None)
        # Assert
        call_kwargs = ctx.channel.send.call_args.kwargs
        embed = call_kwargs["embed"]
        assert embed.color == discord.Color.red()

    @patch("dicebot.commands.stats.get_roll_stats", autospec=True)
    @patch("dicebot.commands.stats.get_ban_stats", autospec=True)
    @patch("dicebot.commands.stats.get_social_stats", autospec=True)
    async def test_stats_embed_is_blue_when_not_banned(
        self, mock_social, mock_ban, mock_roll
    ) -> None:
        """Embed color is blue when the user is not currently banned"""
        # Arrange
        ctx = TestMessageContext.get()
        mock_roll.return_value = {"total": 0, "wins": 0, "losses": 0, "win_rate": "0%", "best": 0, "last_roll": "Never"}
        mock_ban.return_value = {"times_banned": 0, "currently_banned": "No", "immune": "No"}
        mock_social.return_value = {"thanks_given": 0, "thanks_received": 0, "puns_caught": 0}
        # Act
        await stats.stats(ctx, target=None)
        # Assert
        call_kwargs = ctx.channel.send.call_args.kwargs
        embed = call_kwargs["embed"]
        assert embed.color == discord.Color.blue()


class TestGetRollStats(DicebotTestCase):
    async def test_get_roll_stats_no_rolls(self) -> None:
        """Returns zeroed stats when user has no rolls"""
        # Arrange
        ctx = TestMessageContext.get()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        ctx.session.scalars = AsyncMock(return_value=mock_result)
        # Act
        result = await stats.get_roll_stats(ctx.session, ctx.guild, ctx.author)
        # Assert
        assert result["total"] == 0
        assert result["wins"] == 0
        assert result["losses"] == 0
        assert result["win_rate"] == "0%"
        assert result["best"] == 0
        assert result["last_roll"] == "Never"


class TestGetBanStats(DicebotTestCase):
    async def test_get_ban_stats_never_banned(self) -> None:
        """Returns zeroed stats when user has never been banned"""
        # Arrange
        ctx = TestMessageContext.get()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        ctx.session.scalars = AsyncMock(return_value=mock_result)
        ctx.author.is_currently_banned = AsyncMock(return_value=False)
        ctx.author.is_currently_immune = AsyncMock(return_value=False)
        # Act
        result = await stats.get_ban_stats(ctx.session, ctx.guild, ctx.author)
        # Assert
        assert result["times_banned"] == 0
        assert result["currently_banned"] == "No"
        assert result["immune"] == "No"


class TestGetSocialStats(DicebotTestCase):
    async def test_get_social_stats_no_activity(self) -> None:
        """Returns zeroed stats when user has no social activity"""
        # Arrange
        ctx = TestMessageContext.get()
        mock_execute_result = MagicMock()
        mock_execute_result.scalar.return_value = 0
        ctx.session.execute = AsyncMock(return_value=mock_execute_result)
        # Act
        result = await stats.get_social_stats(ctx.session, ctx.guild, ctx.author)
        # Assert
        assert result["thanks_given"] == 0
        assert result["thanks_received"] == 0
        assert result["puns_caught"] == 0
