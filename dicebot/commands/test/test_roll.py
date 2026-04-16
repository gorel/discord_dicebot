#!/usr/bin/env python3

import datetime
from unittest.mock import AsyncMock, MagicMock, create_autospec, patch

from dicebot.commands import roll
from dicebot.data.db.active_event import ActiveEvent, EventType
from dicebot.data.db.roll import Roll
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestRoll(DicebotTestCase):
    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        # Patch ActiveEvent.get_current to return None (no active event) for all roll tests
        # unless a specific test overrides it
        self._active_event_patcher = patch(
            "dicebot.commands.roll.ActiveEvent.get_current",
            new_callable=AsyncMock,
            return_value=None,
        )
        self._active_event_patcher.start()

    async def asyncTearDown(self) -> None:
        self._active_event_patcher.stop()
        await super().asyncTearDown()

    @patch("dicebot.commands.roll.Roll", autospec=True)
    @patch("dicebot.commands.roll.ban", autospec=True)
    async def test_roll_no_gambling(self, mock_ban, mock_roll) -> None:
        with self.subTest("simple"):
            # Arrange
            ctx = TestMessageContext.get()
            ctx.guild.timezone = "US/Pacific"
            ctx.guild.roll_timeout = 0
            ctx.guild.current_roll = 333
            ctx.guild.gambling_limit = None
            mock_last_roll = create_autospec(Roll, rolled_at=datetime.datetime.now())
            mock_roll.get_last_roll = AsyncMock(return_value=mock_last_roll)
            # Act
            with patch("dicebot.commands.roll.random") as mock_random:
                mock_random.randint.return_value = 123
                await roll.roll(ctx, GreedyStr(""))
            # Assert
            mock_roll.assert_called_once()
            mock_ban.ban_internal.assert_not_awaited()
            ctx.session.commit.assert_awaited_once()
            ctx.channel.send.assert_awaited()
        with self.subTest("first roll ever"):
            # Arrange
            mock_roll.reset_mock()
            mock_ban.reset_mock()
            ctx = TestMessageContext.get()
            ctx.guild.roll_timeout = 0
            ctx.guild.current_roll = 333
            ctx.guild.gambling_limit = None
            mock_roll.get_last_roll = AsyncMock(return_value=None)
            # Act
            with patch("dicebot.commands.roll.random") as mock_random:
                mock_random.randint.return_value = 123
                await roll.roll(ctx, GreedyStr(""))
            # Assert
            mock_roll.assert_called_once()
            mock_ban.ban_internal.assert_not_awaited()
            ctx.session.commit.assert_awaited_once()
            ctx.channel.send.assert_awaited()
        with self.subTest("rolled recently"):
            # Arrange
            mock_roll.reset_mock()
            mock_ban.reset_mock()
            ctx = TestMessageContext.get()
            ctx.guild.timezone = "US/Pacific"
            ctx.guild.roll_timeout = 1
            ctx.guild.current_roll = 333
            ctx.guild.gambling_limit = None
            mock_last_roll = create_autospec(Roll, rolled_at=datetime.datetime.now())
            mock_roll.get_last_roll = AsyncMock(return_value=mock_last_roll)
            # Act
            with patch("dicebot.commands.roll.random") as mock_random:
                mock_random.randint.return_value = 123
                await roll.roll(ctx, GreedyStr(""))
            # Assert
            mock_roll.assert_not_called()
            mock_ban.ban_internal.assert_awaited_once()
            ctx.session.commit.assert_not_awaited()
            ctx.channel.send.assert_awaited_once()
        with self.subTest("rolled 1"):
            # Arrange
            mock_roll.reset_mock()
            mock_ban.reset_mock()
            ctx = TestMessageContext.get()
            ctx.guild.roll_timeout = 0
            ctx.guild.current_roll = 333
            ctx.guild.gambling_limit = None
            mock_roll.get_last_roll = AsyncMock(return_value=None)
            # Act
            with patch("dicebot.commands.roll.random") as mock_random:
                mock_random.randint.return_value = 1
                await roll.roll(ctx, GreedyStr(""))
            # Assert
            mock_roll.assert_called_once()
            mock_ban.ban_internal.assert_awaited_once()
            ctx.session.commit.assert_awaited_once()
            ctx.channel.send.assert_awaited()
        with self.subTest("rolled one off"):
            # Arrange
            mock_roll.reset_mock()
            mock_ban.reset_mock()
            ctx = TestMessageContext.get()
            ctx.guild.roll_timeout = 0
            ctx.guild.current_roll = 333
            ctx.guild.allow_renaming = True
            ctx.guild.gambling_limit = None
            mock_roll.get_last_roll = AsyncMock(return_value=None)
            # Act
            with patch("dicebot.commands.roll.random") as mock_random:
                mock_random.randint.return_value = 332
                await roll.roll(ctx, GreedyStr(""))
            # Assert
            mock_roll.assert_called_once()
            mock_ban.ban_internal.assert_not_awaited()
            ctx.session.commit.assert_awaited()
            ctx.channel.send.assert_awaited()
            ctx.guild.add_chat_rename.assert_awaited_once()
            ctx.guild.add_guild_rename.assert_not_awaited()
        with self.subTest("rolled win"):
            # Arrange
            mock_roll.reset_mock()
            mock_ban.reset_mock()
            ctx = TestMessageContext.get()
            ctx.guild.roll_timeout = 0
            ctx.guild.current_roll = 333
            ctx.guild.allow_renaming = True
            ctx.guild.gambling_limit = None
            mock_roll.get_last_roll = AsyncMock(return_value=None)
            # Act
            with patch("dicebot.commands.roll.random") as mock_random:
                mock_random.randint.return_value = 333
                await roll.roll(ctx, GreedyStr(""))
            # Assert
            mock_roll.assert_called_once()
            mock_ban.ban_internal.assert_not_awaited()
            ctx.session.commit.assert_awaited()
            ctx.channel.send.assert_awaited()
            ctx.guild.add_chat_rename.assert_not_awaited()
            ctx.guild.add_guild_rename.assert_awaited_once()

    @patch("dicebot.commands.roll.Roll", autospec=True)
    @patch("dicebot.commands.roll.ban", autospec=True)
    async def test_roll_with_gambling(self, mock_ban, mock_roll) -> None:
        with self.subTest("negative"):
            # Arrange
            mock_roll.reset_mock()
            mock_ban.reset_mock()
            ctx = TestMessageContext.get()
            ctx.guild.roll_timeout = 0
            ctx.guild.current_roll = 333
            ctx.guild.allow_renaming = True
            ctx.guild.gambling_limit = None
            mock_roll.get_last_roll = AsyncMock(return_value=None)
            # Act
            with patch("dicebot.commands.roll.random") as mock_random:
                mock_random.randint.return_value = 333
                await roll.roll(ctx, GreedyStr("-5"))
            # Assert
            mock_roll.assert_not_called()
            mock_ban.ban_internal.assert_awaited_once()
            ctx.session.commit.assert_not_awaited()
            ctx.channel.send.assert_awaited()
            ctx.guild.add_chat_rename.assert_not_awaited()
            ctx.guild.add_guild_rename.assert_not_awaited()
        with self.subTest("too high"):
            # Arrange
            mock_roll.reset_mock()
            mock_ban.reset_mock()
            ctx = TestMessageContext.get()
            ctx.guild.roll_timeout = 0
            ctx.guild.current_roll = 333
            ctx.guild.allow_renaming = True
            ctx.guild.gambling_limit = None
            mock_roll.get_last_roll = AsyncMock(return_value=None)
            # Act
            with patch("dicebot.commands.roll.random") as mock_random:
                mock_random.randint.return_value = 333
                await roll.roll(ctx, GreedyStr("334"))
            # Assert
            mock_roll.assert_not_called()
            mock_ban.ban_internal.assert_not_awaited()
            ctx.session.commit.assert_not_awaited()
            ctx.channel.send.assert_awaited()
            ctx.guild.add_chat_rename.assert_not_awaited()
            ctx.guild.add_guild_rename.assert_not_awaited()
        with self.subTest("turboban"):
            # Arrange
            mock_roll.reset_mock()
            mock_ban.reset_mock()
            ctx = TestMessageContext.get()
            ctx.guild.roll_timeout = 0
            ctx.guild.current_roll = 333
            ctx.guild.allow_renaming = True
            ctx.guild.gambling_limit = None
            mock_roll.get_last_roll = AsyncMock(return_value=None)
            # Act
            with patch("dicebot.commands.roll.random") as mock_random:
                mock_random.randint.return_value = 123
                await roll.roll(ctx, GreedyStr("5"))
            # Assert
            mock_roll.assert_called()
            self.assertEqual(5, mock_roll.call_count)
            mock_ban.ban_internal.assert_not_awaited()
            mock_ban.turboban.assert_awaited_once()
            ctx.session.commit.assert_awaited()
            ctx.channel.send.assert_awaited()
            ctx.guild.add_chat_rename.assert_not_awaited()
            ctx.guild.add_guild_rename.assert_not_awaited()

    @patch("dicebot.commands.roll.roast", autospec=True)
    @patch("dicebot.commands.roll.Roll", autospec=True)
    @patch("dicebot.commands.roll.ban", autospec=True)
    @patch("dicebot.commands.roll.ActiveEvent.get_current", new_callable=AsyncMock, return_value=None)
    async def test_roll_critical_fail_calls_roast(self, mock_event, mock_ban, mock_roll, mock_roast):
        # Arrange
        ctx = TestMessageContext.get()
        ctx.guild.roll_timeout = 0
        ctx.guild.current_roll = 10
        ctx.guild.gambling_limit = None
        mock_roll.get_last_roll = AsyncMock(return_value=None)
        # Act
        with patch("dicebot.commands.roll.random") as mock_random:
            mock_random.randint.return_value = 1
            await roll.roll(ctx, GreedyStr(""))
        # Assert
        mock_roast.generate_roast.assert_awaited_once()

    async def test_set_gambling_limit(self) -> None:
        with self.subTest("simple"):
            # Arrange
            ctx = TestMessageContext.get()
            # Act
            await roll.set_gambling_limit(ctx, 123)
            # Assert
            self.assertEqual(123, ctx.guild.gambling_limit)
            ctx.session.commit.assert_awaited_once()
            ctx.channel.send.assert_awaited_once()
        with self.subTest("negative"):
            # Arrange
            ctx = TestMessageContext.get()
            # Act
            await roll.set_gambling_limit(ctx, -1)
            # Assert
            self.assertIsNone(ctx.guild.gambling_limit)
            ctx.session.commit.assert_awaited_once()
            ctx.channel.send.assert_awaited_once()


class TestRollEvents(DicebotTestCase):
    def _make_mock_event(self, event_type: EventType) -> MagicMock:
        mock_event = MagicMock(spec=ActiveEvent)
        mock_event.event_type_enum = event_type
        return mock_event

    @patch("dicebot.commands.roll.Roll", autospec=True)
    @patch("dicebot.commands.roll.ban", autospec=True)
    @patch("dicebot.commands.roll.ActiveEvent.get_current", new_callable=AsyncMock)
    async def test_roll_curse_day_under_5(self, mock_get_current, mock_ban, mock_roll) -> None:
        """CURSE_DAY: roll=3 should be treated as a critical fail (ban triggered)"""
        # Arrange
        ctx = TestMessageContext.get()
        ctx.guild.roll_timeout = 0
        ctx.guild.current_roll = 20
        ctx.guild.gambling_limit = None
        mock_roll.get_last_roll = AsyncMock(return_value=None)
        mock_get_current.return_value = self._make_mock_event(EventType.CURSE_DAY)
        # Act
        with patch("dicebot.commands.roll.random") as mock_random:
            mock_random.randint.return_value = 3  # < 5, should be treated as 1
            await roll.roll(ctx, GreedyStr(""))
        # Assert — ban should be called because effective_roll == 1
        mock_ban.ban_internal.assert_awaited_once()

    @patch("dicebot.commands.roll.Roll", autospec=True)
    @patch("dicebot.commands.roll.ban", autospec=True)
    @patch("dicebot.commands.roll.ActiveEvent.get_current", new_callable=AsyncMock)
    async def test_roll_curse_day_exactly_1(self, mock_get_current, mock_ban, mock_roll) -> None:
        """CURSE_DAY: roll=1 should still be a normal critical fail (ban triggered, no double effect)"""
        # Arrange
        ctx = TestMessageContext.get()
        ctx.guild.roll_timeout = 0
        ctx.guild.current_roll = 20
        ctx.guild.gambling_limit = None
        mock_roll.get_last_roll = AsyncMock(return_value=None)
        mock_get_current.return_value = self._make_mock_event(EventType.CURSE_DAY)
        # Act
        with patch("dicebot.commands.roll.random") as mock_random:
            mock_random.randint.return_value = 1
            await roll.roll(ctx, GreedyStr(""))
        # Assert — ban should be called for the natural 1
        mock_ban.ban_internal.assert_awaited_once()

    @patch("dicebot.commands.roll.Roll", autospec=True)
    @patch("dicebot.commands.roll.ban", autospec=True)
    @patch("dicebot.commands.roll.ActiveEvent.get_current", new_callable=AsyncMock)
    async def test_roll_blessing_day_near_max(self, mock_get_current, mock_ban, mock_roll) -> None:
        """BLESSING_DAY: roll=next_roll-1 (one off) should be treated as a win"""
        # Arrange
        ctx = TestMessageContext.get()
        ctx.guild.roll_timeout = 0
        ctx.guild.current_roll = 20
        ctx.guild.allow_renaming = True
        ctx.guild.gambling_limit = None
        mock_roll.get_last_roll = AsyncMock(return_value=None)
        mock_get_current.return_value = self._make_mock_event(EventType.BLESSING_DAY)
        # Act
        with patch("dicebot.commands.roll.random") as mock_random:
            mock_random.randint.return_value = 19  # next_roll - 1 = 19, within range
            await roll.roll(ctx, GreedyStr(""))
        # Assert — treated as win, so add_guild_rename should be called
        mock_ban.ban_internal.assert_not_awaited()
        ctx.guild.add_guild_rename.assert_awaited_once()

    @patch("dicebot.commands.roll.Roll", autospec=True)
    @patch("dicebot.commands.roll.ban", autospec=True)
    @patch("dicebot.commands.roll.ActiveEvent.get_current", new_callable=AsyncMock)
    async def test_roll_no_event(self, mock_get_current, mock_ban, mock_roll) -> None:
        """No event: roll=3 should be a normal no-match (no ban, no rename)"""
        # Arrange
        ctx = TestMessageContext.get()
        ctx.guild.roll_timeout = 0
        ctx.guild.current_roll = 20
        ctx.guild.allow_renaming = True
        ctx.guild.gambling_limit = None
        mock_roll.get_last_roll = AsyncMock(return_value=None)
        mock_get_current.return_value = None
        # Act
        with patch("dicebot.commands.roll.random") as mock_random:
            mock_random.randint.return_value = 3
            await roll.roll(ctx, GreedyStr(""))
        # Assert — normal no-match: no ban, no rename
        mock_ban.ban_internal.assert_not_awaited()
        ctx.guild.add_guild_rename.assert_not_awaited()
        ctx.guild.add_chat_rename.assert_not_awaited()
