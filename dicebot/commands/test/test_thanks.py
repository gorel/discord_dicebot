#!/usr/bin/env python3

from dicebot.commands import thanks
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestThanks(DicebotTestCase):
    async def test_extract_targets(self) -> None:
        # Arrange
        tests = [
            ("to <@123> for helping me out!", [123]),
            ("to <@123> and <@456> for helping me out!", [123, 456]),
            ("to @everyone for helping me out!", []),
        ]
        for msg, expected in tests:
            # Act
            actual = thanks.extract_targets(msg)
            # Assert
            self.assertEqual(expected, actual)

    async def test_thanks(self) -> None:
        with self.subTest("simple"):
            # Arrange
            ctx = TestMessageContext.get()
            reason = GreedyStr("to <@123> for helping me out!")
            # Act
            await thanks.thanks(ctx, reason)
            # Assert
            ctx.session.add_all.assert_called_once()
            ctx.session.commit.assert_awaited_once()
            ctx.channel.send.assert_awaited_once()
        with self.subTest("no targets"):
            # Arrange
            ctx = TestMessageContext.get()
            reason = GreedyStr("you for helping me out!")
            # Act
            await thanks.thanks(ctx, reason)
            # Assert
            ctx.session.add_all.assert_not_called()
            ctx.session.commit.assert_not_awaited()
            ctx.channel.send.assert_awaited_once()

    async def test_thanks_scoreboard(self) -> None:
        # Arrange
        ctx = TestMessageContext.get()
        # Act
        await thanks.thanks_scoreboard(ctx)
        # Assert
        ctx.guild.thanks_scoreboard_str.assert_awaited_once()
        ctx.channel.send.assert_awaited_once()
