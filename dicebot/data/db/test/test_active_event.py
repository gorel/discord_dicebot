#!/usr/bin/env python3

import datetime
import unittest

from sqlalchemy import BigInteger, Integer
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from dicebot.data.db.active_event import ActiveEvent, EventType
from dicebot.data.db.base import Base

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


class TestActiveEvent(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as conn:
            await _create_tables(conn)
        self.session = AsyncSession(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.session.close()
        await self.engine.dispose()

    async def test_get_current_no_event(self):
        """get_current returns None when no rows exist."""
        result = await ActiveEvent.get_current(self.session, guild_id=1)
        self.assertIsNone(result)

    async def test_get_current_expired(self):
        """get_current returns None when only expired events exist."""
        expired_event = ActiveEvent(
            guild_id=1,
            event_type=EventType.LUCKY_HOUR.value,
            started_at=datetime.datetime.now() - datetime.timedelta(hours=2),
            expires_at=datetime.datetime.now() - datetime.timedelta(hours=1),
        )
        self.session.add(expired_event)
        await self.session.commit()

        result = await ActiveEvent.get_current(self.session, guild_id=1)
        self.assertIsNone(result)

    async def test_get_current_active(self):
        """get_current returns the event when one is active (expires_at in future)."""
        active_event = ActiveEvent(
            guild_id=1,
            event_type=EventType.CURSE_DAY.value,
            started_at=datetime.datetime.now() - datetime.timedelta(minutes=30),
            expires_at=datetime.datetime.now() + datetime.timedelta(hours=1),
        )
        self.session.add(active_event)
        await self.session.commit()

        result = await ActiveEvent.get_current(self.session, guild_id=1)
        self.assertIsNotNone(result)
        self.assertEqual(result.event_type, EventType.CURSE_DAY.value)

    async def test_event_type_enum(self):
        """event_type_enum property returns the correct EventType."""
        event = ActiveEvent(
            guild_id=1,
            event_type=EventType.BLESSING_DAY.value,
            started_at=datetime.datetime.now(),
            expires_at=datetime.datetime.now() + datetime.timedelta(hours=1),
        )
        self.session.add(event)
        await self.session.commit()

        result = await ActiveEvent.get_current(self.session, guild_id=1)
        self.assertIsNotNone(result)
        self.assertEqual(result.event_type_enum, EventType.BLESSING_DAY)


if __name__ == "__main__":
    unittest.main()
