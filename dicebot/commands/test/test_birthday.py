#!/usr/bin/env python3

import datetime

from dicebot.commands import birthday
from dicebot.data.types.greedy_str import GreedyStr
from dicebot.test.utils import DicebotTestCase, TestMessageContext


class TestBirthday(DicebotTestCase):
    async def test_birthday(self) -> None:
        with self.subTest("valid"):
            # Arrange
            ctx = TestMessageContext.get()
            now = datetime.datetime.now()
            birthday_str = "July 5"
            expected = datetime.datetime(year=now.year, month=7, day=5)
            # Act
            await birthday.birthday(ctx, GreedyStr(birthday_str))
            # Assert
            self.assertEqual(expected, ctx.author.birthday)
            ctx.session.commit.assert_awaited()
            ctx.send.assert_awaited_once()
        with self.subTest("invalid"):
            # Arrange
            ctx = TestMessageContext.get()
            now = datetime.datetime.now()
            birthday_str = "Octuembre 32"
            # Act
            await birthday.birthday(ctx, GreedyStr(birthday_str))
            # Assert
            ctx.session.commit.assert_not_awaited()
            ctx.send.assert_awaited_once()
