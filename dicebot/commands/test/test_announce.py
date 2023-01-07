#!/usr/bin/env python3

from unittest.mock import AsyncMock, create_autospec, patch

import discord
from discord import TextChannel, VoiceChannel

from dicebot.commands import announce
from dicebot.data.db.guild import Guild
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestAnnounce(DicebotTestCase):
    async def test_announce(self) -> None:
        with self.subTest("simple"):
            # Arrange
            ctx = TestMessageContext.get()
            ctx.guild.id = 111
            mock_guilds = [create_autospec(Guild, id=111, primary_text_channel=999)]
            mock_fetched_guild = create_autospec(discord.Guild)
            ctx.client.fetch_guild = AsyncMock(return_value=mock_fetched_guild)
            mock_channel = create_autospec(TextChannel)
            mock_fetched_guild.fetch_channel = AsyncMock(return_value=mock_channel)
            with patch(
                "dicebot.commands.announce.Guild",
                get_all_for_announcements=AsyncMock(return_value=mock_guilds),
            ):
                # Act
                await announce.announce(ctx, GreedyStr("hello world"))
                # Assert
                mock_channel.send.assert_awaited_once()

        with self.subTest("extra guilds in test mode"):
            # Arrange
            ctx = TestMessageContext.get()
            ctx.guild.id = 111
            mock_guilds = [
                create_autospec(Guild, id=111, primary_text_channel=999),
                create_autospec(Guild, id=222, primary_text_channel=888),
            ]
            mock_fetched_guild = create_autospec(discord.Guild)
            ctx.client.fetch_guild = AsyncMock(return_value=mock_fetched_guild)
            mock_channel = create_autospec(TextChannel)
            mock_fetched_guild.fetch_channel = AsyncMock(return_value=mock_channel)
            with patch(
                "dicebot.commands.announce.Guild",
                get_all_for_announcements=AsyncMock(return_value=mock_guilds),
            ):
                # Act
                await announce.announce(ctx, GreedyStr("hello world"))
                # Assert
                mock_channel.send.assert_awaited_once()

        with self.subTest("non-text primary channel"):
            # Arrange
            ctx = TestMessageContext.get()
            ctx.guild.id = 111
            mock_guilds = [create_autospec(Guild, id=111, primary_text_channel=999)]
            mock_fetched_guild = create_autospec(discord.Guild)
            ctx.client.fetch_guild = AsyncMock(return_value=mock_fetched_guild)
            mock_channel = create_autospec(VoiceChannel)
            mock_fetched_guild.fetch_channel = AsyncMock(return_value=mock_channel)
            mock_fetched_channels = [
                create_autospec(VoiceChannel),
                create_autospec(TextChannel),
            ]
            mock_fetched_guild.fetch_channels = AsyncMock(
                return_value=mock_fetched_channels
            )
            with patch(
                "dicebot.commands.announce.Guild",
                get_all_for_announcements=AsyncMock(return_value=mock_guilds),
            ):
                # Act
                await announce.announce(ctx, GreedyStr("hello world"))
                # Assert
                # Expect two because we'll also send the help message
                self.assertEqual(2, len(mock_fetched_channels[1].send.await_args_list))

        with self.subTest("primary channel deleted"):
            # Arrange
            ctx = TestMessageContext.get()
            ctx.guild.id = 111
            mock_guilds = [create_autospec(Guild, id=111, primary_text_channel=None)]
            mock_fetched_guild = create_autospec(discord.Guild)
            ctx.client.fetch_guild = AsyncMock(return_value=mock_fetched_guild)
            mock_fetched_channels = [
                create_autospec(VoiceChannel),
                create_autospec(TextChannel),
            ]
            mock_fetched_guild.fetch_channels = AsyncMock(
                return_value=mock_fetched_channels
            )
            with patch(
                "dicebot.commands.announce.Guild",
                get_all_for_announcements=AsyncMock(return_value=mock_guilds),
            ):
                # Act
                await announce.announce(ctx, GreedyStr("hello world"))
                # Assert
                # Expect two because we'll also send the help message
                self.assertEqual(2, len(mock_fetched_channels[1].send.await_args_list))

        with self.subTest("no text channels"):
            # Arrange
            ctx = TestMessageContext.get()
            ctx.guild.id = 111
            mock_guilds = [create_autospec(Guild, id=111, primary_text_channel=None)]
            mock_fetched_guild = create_autospec(discord.Guild)
            ctx.client.fetch_guild = AsyncMock(return_value=mock_fetched_guild)
            mock_channel = create_autospec(VoiceChannel)
            mock_fetched_guild.fetch_channel = AsyncMock(return_value=mock_channel)
            mock_fetched_guild.fetch_channels = AsyncMock(return_value=[])
            with patch(
                "dicebot.commands.announce.Guild",
                get_all_for_announcements=AsyncMock(return_value=mock_guilds),
            ):
                # Act
                await announce.announce(ctx, GreedyStr("hello world"))
                # Assert
                mock_channel.send.assert_not_awaited()

    async def test_set_announce_channel(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        # Act
        await announce.set_announce_channel(ctx)
        # Assert
        ctx.channel.send.assert_awaited_once()
        self.assertEqual(ctx.channel.id, ctx.guild.primary_text_channel)
        ctx.session.commit.assert_awaited_once()

    async def test_disable_announcements(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        # Act
        await announce.disable_announcements(ctx)
        # Assert
        ctx.channel.send.assert_awaited_once()
        self.assertTrue(ctx.guild.disable_announcements)
        ctx.session.commit.assert_awaited_once()
