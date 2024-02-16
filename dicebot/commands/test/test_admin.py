#!/usr/bin/env python3

from unittest.mock import AsyncMock, create_autospec, patch

from dicebot.commands import admin
from dicebot.data.db.channel import Channel
from dicebot.data.db.user import User
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.data.types.set_message_subcommand import SetMessageSubcommand
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestAdmin(DicebotTestCase):
    async def test_requires_owner(self) -> None:
        with self.subTest("is owner"):
            # Arrange
            ctx = TestMessageContext.get()
            inner_coro = AsyncMock()
            coro = admin.requires_owner(inner_coro)
            # Act
            with patch("dicebot.commands.admin.os") as mock_os:
                mock_os.getenv.return_value = ctx.author.id
                await coro(ctx)
            # Assert
            inner_coro.assert_awaited_once()
        with self.subTest("not owner"):
            # Arrange
            ctx = TestMessageContext.get()
            inner_coro = AsyncMock()
            coro = admin.requires_owner(inner_coro)
            # Act
            with patch("dicebot.commands.admin.os") as mock_os:
                mock_os.getenv.return_value = ctx.author.id + 1
                await coro(ctx)
            # Assert
            inner_coro.assert_not_awaited()

    async def test_requires_admin(self) -> None:
        with self.subTest("is admin"):
            # Arrange
            ctx = TestMessageContext.get()
            ctx.author.is_admin_of.return_value = True
            inner_coro = AsyncMock()
            coro = admin.requires_admin(inner_coro)
            # Act
            await coro(ctx)
            # Assert
            inner_coro.assert_awaited_once()
        with self.subTest("not admin"):
            # Arrange
            ctx = TestMessageContext.get()
            ctx.author.is_admin_of.return_value = False
            inner_coro = AsyncMock()
            coro = admin.requires_admin(inner_coro)
            # Act
            await coro(ctx)
            # Assert
            inner_coro.assert_not_awaited()

    async def test_add_admin(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        target = create_autospec(User)
        # Act
        await admin.add_admin(ctx, target)
        # Assert
        ctx.guild.admins.append.assert_called_once_with(target)
        ctx.session.commit.assert_awaited()
        ctx.channel.send.assert_awaited_once()

    async def test_remove_admin(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        ctx.guild.admins.__len__.return_value = 2
        target = create_autospec(User)
        # Act
        await admin.remove_admin(ctx, target)
        # Assert
        ctx.guild.admins.remove.assert_called_once_with(target)
        ctx.session.commit.assert_awaited()
        ctx.channel.send.assert_awaited_once()

    async def test_remove_admin_only_one_left(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        ctx.guild.admins.__len__.return_value = 1
        target = create_autospec(User)
        # Act
        await admin.remove_admin(ctx, target)
        # Assert
        ctx.channel.send.assert_awaited_once()
        ctx.guild.admins.remove.assert_not_called()
        ctx.session.commit.assert_not_awaited()

    async def test_set_msg(self) -> None:
        with self.subTest("win"):
            # Arrange
            ctx = TestMessageContext.get()
            # Act
            await admin.set_msg(ctx, SetMessageSubcommand.WIN, msg=GreedyStr("win"))
            # Assert
            ctx.channel.send.assert_awaited_once()
            self.assertEqual("win", ctx.guild.critical_success_msg)
            ctx.session.commit.assert_awaited_once()
        with self.subTest("lose"):
            # Arrange
            ctx = TestMessageContext.get()
            # Act
            await admin.set_msg(ctx, SetMessageSubcommand.LOSE, msg=GreedyStr("lose"))
            # Assert
            ctx.channel.send.assert_awaited_once()
            self.assertEqual("lose", ctx.guild.critical_failure_msg)
            ctx.session.commit.assert_awaited_once()

    async def test_set_reaction_threshold(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        # Act
        await admin.set_reaction_threshold(ctx, 123)
        # Assert
        ctx.channel.send.assert_awaited_once()
        self.assertEqual(123, ctx.guild.reaction_threshold)
        ctx.session.commit.assert_awaited_once()

    async def test_set_timeout(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        # Act
        await admin.set_timeout(ctx, 456)
        # Assert
        ctx.channel.send.assert_awaited_once()
        self.assertEqual(456, ctx.guild.roll_timeout)
        ctx.session.commit.assert_awaited_once()

    async def test_set_turbo_ban_timing_threshold(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        # Act
        await admin.set_turbo_ban_timing_threshold(ctx, 789)
        # Assert
        ctx.channel.send.assert_awaited_once()
        self.assertEqual(789, ctx.guild.turboban_threshold)
        ctx.session.commit.assert_awaited_once()

    async def test_toggle_shame(self) -> None:
        mock_channel = create_autospec(Channel, shame=False)
        with patch(
            "dicebot.commands.admin.Channel",
            get_or_create=AsyncMock(return_value=mock_channel),
        ):
            # Arrange
            ctx = TestMessageContext.get()
            # Act
            await admin.toggle_shame(ctx)
            # Assert
            ctx.channel.send.assert_awaited_once()
            self.assertTrue(mock_channel.shame)
            ctx.session.commit.assert_awaited_once()
