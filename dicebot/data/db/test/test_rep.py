#!/usr/bin/env python3

import unittest

from sqlalchemy import BigInteger, Integer
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from dicebot.data.db.base import Base
from dicebot.data.db.rep import Rep

# Import all models so their tables are registered in Base.metadata before create_all
import dicebot.data.db.guild  # noqa: F401


async def _create_tables(conn):
    """Create all tables, replacing BigInteger with Integer for SQLite compatibility."""

    def _create(connection):
        for table in Base.metadata.sorted_tables:
            # Replace BigInteger with Integer for SQLite (needed for PK autoincrement)
            cols_to_fix = [
                col for col in table.columns
                if isinstance(col.type, BigInteger)
            ]
            original_types = {col.name: col.type for col in cols_to_fix}
            for col in cols_to_fix:
                col.type = Integer()
            try:
                table.create(connection, checkfirst=True)
            finally:
                for col in cols_to_fix:
                    col.type = original_types[col.name]

    await conn.run_sync(_create)


GUILD_ID = 1
USER_A = 101
USER_B = 102
USER_C = 103


class TestRep(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as conn:
            await _create_tables(conn)
        self.session = AsyncSession(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.session.close()
        await self.engine.dispose()

    async def test_give_and_get_total_received(self):
        """give records rep and get_total_received returns the correct sum."""
        await Rep.give(self.session, guild_id=GUILD_ID, giver_id=USER_A, receiver_id=USER_B, amount=10)
        total = await Rep.get_total_received(self.session, guild_id=GUILD_ID, user_id=USER_B)
        self.assertEqual(total, 10)

    async def test_get_total_received_no_rep(self):
        """get_total_received returns 0 when the user has received no rep."""
        total = await Rep.get_total_received(self.session, guild_id=GUILD_ID, user_id=USER_A)
        self.assertEqual(total, 0)

    async def test_get_total_given(self):
        """get_total_given returns the sum of rep given by a user."""
        await Rep.give(self.session, guild_id=GUILD_ID, giver_id=USER_A, receiver_id=USER_B, amount=5)
        total = await Rep.get_total_given(self.session, guild_id=GUILD_ID, user_id=USER_A)
        self.assertEqual(total, 5)

    async def test_get_biggest_fan(self):
        """get_biggest_fan returns (giver_id, total) for the top giver."""
        await Rep.give(self.session, guild_id=GUILD_ID, giver_id=USER_A, receiver_id=USER_C, amount=10)
        await Rep.give(self.session, guild_id=GUILD_ID, giver_id=USER_B, receiver_id=USER_C, amount=3)
        result = await Rep.get_biggest_fan(self.session, guild_id=GUILD_ID, user_id=USER_C)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], USER_A)
        self.assertEqual(result[1], 10)

    async def test_get_biggest_fan_none(self):
        """get_biggest_fan returns None when no rep has been given to this user."""
        result = await Rep.get_biggest_fan(self.session, guild_id=GUILD_ID, user_id=USER_C)
        self.assertIsNone(result)

    async def test_get_biggest_fan_none_when_net_negative(self):
        """get_biggest_fan returns None when the top giver has a net-negative total."""
        await Rep.give(self.session, guild_id=GUILD_ID, giver_id=USER_A, receiver_id=USER_C, amount=1)
        await Rep.give(self.session, guild_id=GUILD_ID, giver_id=USER_A, receiver_id=USER_C, amount=-5)
        result = await Rep.get_biggest_fan(self.session, guild_id=GUILD_ID, user_id=USER_C)
        self.assertIsNone(result)

    async def test_get_hater(self):
        """get_hater returns (giver_id, total) for the person who gave the most negative rep."""
        await Rep.give(self.session, guild_id=GUILD_ID, giver_id=USER_A, receiver_id=USER_C, amount=-5)
        await Rep.give(self.session, guild_id=GUILD_ID, giver_id=USER_B, receiver_id=USER_C, amount=3)
        result = await Rep.get_hater(self.session, guild_id=GUILD_ID, user_id=USER_C)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], USER_A)
        self.assertEqual(result[1], -5)

    async def test_get_hater_none_when_all_positive(self):
        """get_hater returns None when all givers are net positive."""
        await Rep.give(self.session, guild_id=GUILD_ID, giver_id=USER_A, receiver_id=USER_C, amount=5)
        await Rep.give(self.session, guild_id=GUILD_ID, giver_id=USER_B, receiver_id=USER_C, amount=3)
        result = await Rep.get_hater(self.session, guild_id=GUILD_ID, user_id=USER_C)
        self.assertIsNone(result)

    async def test_get_best_friend(self):
        """get_best_friend returns (receiver_id, total) for the top recipient of a user's rep."""
        await Rep.give(self.session, guild_id=GUILD_ID, giver_id=USER_A, receiver_id=USER_B, amount=10)
        await Rep.give(self.session, guild_id=GUILD_ID, giver_id=USER_A, receiver_id=USER_C, amount=3)
        result = await Rep.get_best_friend(self.session, guild_id=GUILD_ID, user_id=USER_A)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], USER_B)
        self.assertEqual(result[1], 10)

    async def test_get_best_friend_none(self):
        """get_best_friend returns None when the user has given no rep."""
        result = await Rep.get_best_friend(self.session, guild_id=GUILD_ID, user_id=USER_A)
        self.assertIsNone(result)

    async def test_get_best_friend_none_when_net_negative(self):
        """get_best_friend returns None when the top recipient has a net-negative total."""
        await Rep.give(self.session, guild_id=GUILD_ID, giver_id=USER_A, receiver_id=USER_B, amount=1)
        await Rep.give(self.session, guild_id=GUILD_ID, giver_id=USER_A, receiver_id=USER_B, amount=-5)
        result = await Rep.get_best_friend(self.session, guild_id=GUILD_ID, user_id=USER_A)
        self.assertIsNone(result)

    async def test_get_nemesis(self):
        """get_nemesis returns (receiver_id, total) for the recipient with the most negative net rep."""
        await Rep.give(self.session, guild_id=GUILD_ID, giver_id=USER_A, receiver_id=USER_B, amount=-5)
        await Rep.give(self.session, guild_id=GUILD_ID, giver_id=USER_A, receiver_id=USER_C, amount=3)
        result = await Rep.get_nemesis(self.session, guild_id=GUILD_ID, user_id=USER_A)
        self.assertIsNotNone(result)
        self.assertEqual(result[0], USER_B)
        self.assertEqual(result[1], -5)

    async def test_get_nemesis_none_when_all_positive(self):
        """get_nemesis returns None when all recipients have net positive rep from this user."""
        await Rep.give(self.session, guild_id=GUILD_ID, giver_id=USER_A, receiver_id=USER_B, amount=5)
        await Rep.give(self.session, guild_id=GUILD_ID, giver_id=USER_A, receiver_id=USER_C, amount=3)
        result = await Rep.get_nemesis(self.session, guild_id=GUILD_ID, user_id=USER_A)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
