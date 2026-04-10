#!/usr/bin/env python3

import datetime
from unittest.mock import AsyncMock, create_autospec, patch

from dicebot.commands import ban_immunity
from dicebot.data.db.ban_immunity import BanImmunity
from dicebot.data.db.user import User
from dicebot.data.types.time import Time
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestIsCurrentlyImmune(DicebotTestCase):
    @patch("dicebot.data.db.ban_immunity.BanImmunity.get_active", new_callable=AsyncMock)
    async def test_is_currently_immune_true(self, mock_get_active) -> None:
        # Arrange
        user = User(id=12345)
        ctx = TestMessageContext.get()
        ctx.author = user
        immunity_obj = create_autospec(BanImmunity)
        mock_get_active.return_value = immunity_obj
        # Act
        result = await user.is_currently_immune(ctx.session, ctx.guild)
        # Assert
        assert result is True

    @patch("dicebot.data.db.ban_immunity.BanImmunity.get_active", new_callable=AsyncMock)
    async def test_is_currently_immune_false(self, mock_get_active) -> None:
        # Arrange
        user = User(id=12345)
        ctx = TestMessageContext.get()
        ctx.author = user
        mock_get_active.return_value = None
        # Act
        result = await user.is_currently_immune(ctx.session, ctx.guild)
        # Assert
        assert result is False


class TestGrantImmunity(DicebotTestCase):
    @patch("dicebot.commands.ban_immunity.BanImmunity.grant", autospec=True)
    @patch("dicebot.commands.ban_immunity.timezone")
    async def test_grant_immunity_sends_confirmation(self, mock_tz, mock_grant) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        target = create_autospec(User)
        target.is_currently_banned = AsyncMock(return_value=False)
        timer = create_autospec(Time, seconds=3600)
        mock_immunity = create_autospec(BanImmunity)
        mock_immunity.immune_until = datetime.datetime.now() + datetime.timedelta(hours=1)
        mock_grant.return_value = mock_immunity
        # Act
        await ban_immunity.grant_immunity(ctx, target, timer)
        # Assert
        mock_grant.assert_awaited_once()
        ctx.message.channel.send.assert_awaited_once()

    @patch("dicebot.commands.ban_immunity.unban_internal", autospec=True)
    @patch("dicebot.commands.ban_immunity.BanImmunity.grant", autospec=True)
    @patch("dicebot.commands.ban_immunity.timezone")
    async def test_grant_immunity_unbans_if_banned(
        self, mock_tz, mock_grant, mock_unban
    ) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        target = create_autospec(User)
        target.is_currently_banned = AsyncMock(return_value=True)
        timer = create_autospec(Time, seconds=3600)
        mock_immunity = create_autospec(BanImmunity)
        mock_immunity.immune_until = datetime.datetime.now() + datetime.timedelta(hours=1)
        mock_grant.return_value = mock_immunity
        # Act
        await ban_immunity.grant_immunity(ctx, target, timer)
        # Assert
        ctx.message.channel.send.assert_awaited_once()
        mock_unban.assert_awaited_once()
