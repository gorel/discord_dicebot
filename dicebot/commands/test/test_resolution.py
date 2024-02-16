#!/usr/bin/env python3

import datetime
from unittest.mock import AsyncMock, create_autospec, patch

from dicebot.commands import resolution
from dicebot.data.db.resolution import Resolution
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestResolution(DicebotTestCase):
    @patch("dicebot.commands.resolution.Resolution")
    @patch("dicebot.commands.resolution.remind_task")
    async def test_resolution(self, mock_remind_task, mock_resolution) -> None:
        with self.subTest("simple"):
            # Arrange
            ctx = TestMessageContext.get()
            # Act
            await resolution.resolution(ctx, "yearly", GreedyStr("my resolution"))
            # Assert
            mock_resolution.assert_called_once()
            mock_remind_task.apply_async.assert_called_once()
            ctx.session.commit.assert_awaited_once()
            ctx.session.refresh.assert_awaited_once()
            ctx.channel.send.assert_awaited_once()
        with self.subTest("invalid"):
            # Arrange
            mock_resolution.reset_mock()
            mock_remind_task.reset_mock()
            ctx = TestMessageContext.get()
            # Act
            await resolution.resolution(ctx, "whenever", GreedyStr("my resolution"))
            # Assert
            mock_resolution.assert_not_called()
            mock_remind_task.apply_async.assert_not_called()
            ctx.channel.send.assert_awaited_once()

    @patch("dicebot.commands.resolution.Resolution")
    async def test_my_resolutions(self, mock_resolution) -> None:
        with self.subTest("simple"):
            # Arrange
            ctx = TestMessageContext.get()
            ctx.guild.timezone = "US/Pacific"
            mock_resolution.get_all_for_user = AsyncMock(
                return_value=[
                    create_autospec(Resolution, created_at=datetime.datetime.now())
                ]
            )
            # Act
            await resolution.my_resolutions(ctx)
            # Assert
            mock_resolution.get_all_for_user.assert_awaited_once()
            ctx.channel.send.assert_awaited_once()
            self.assertIn("Your resolutions", ctx.channel.send.await_args.args[0])
        with self.subTest("no resolutions"):
            # Arrange
            ctx = TestMessageContext.get()
            ctx.guild.timezone = "US/Pacific"
            mock_resolution.get_all_for_user = AsyncMock(return_value=[])
            # Act
            await resolution.my_resolutions(ctx)
            # Assert
            mock_resolution.get_all_for_user.assert_awaited_once()
            ctx.channel.send.assert_awaited_once()
            self.assertNotIn("Your resolutions", ctx.channel.send.await_args.args[0])
    @patch("dicebot.commands.resolution.Resolution")
    async def test_delete_resolution(self, mock_resolution) -> None:
        with self.subTest("simple"):
            # Arrange
            ctx = TestMessageContext.get()
            ctx.guild.timezone = "US/Pacific"
            mock_res = create_autospec(
                Resolution, author_id=ctx.author_id, created_at=datetime.datetime.now()
            )
            mock_resolution.get_or_none = AsyncMock(return_value=mock_res)
            # Act
            await resolution.delete_resolution(ctx, 123)
            # Assert
            mock_resolution.get_or_none.assert_awaited_once()
            self.assertFalse(mock_res.active)
            ctx.session.commit.assert_awaited_once()
            ctx.channel.send.assert_awaited_once()
        with self.subTest("bad resolution id"):
            # Arrange
            ctx = TestMessageContext.get()
            mock_resolution.get_or_none = AsyncMock(return_value=None)
            # Act
            await resolution.delete_resolution(ctx, 123)
            # Assert
            mock_resolution.get_or_none.assert_awaited_once()
            ctx.session.commit.assert_not_awaited()
            ctx.channel.send.assert_awaited_once()
        with self.subTest("not the author"):
            # Arrange
            ctx = TestMessageContext.get()
            mock_res = create_autospec(Resolution, author_id=ctx.author_id + 1)
            mock_resolution.get_or_none = AsyncMock(return_value=mock_res)
            # Act
            await resolution.delete_resolution(ctx, 123)
            # Assert
            mock_resolution.get_or_none.assert_awaited_once()
            ctx.session.commit.assert_not_awaited()
            ctx.channel.send.assert_awaited_once()
