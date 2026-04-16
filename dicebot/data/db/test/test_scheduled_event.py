#!/usr/bin/env python3

import datetime
import unittest

from sqlalchemy import BigInteger, Integer
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from dicebot.data.db.base import Base
from dicebot.data.db.scheduled_event import ScheduledEvent, ScheduledEventSignup

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


class TestScheduledEvent(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with self.engine.begin() as conn:
            await _create_tables(conn)
        self.session = AsyncSession(self.engine, expire_on_commit=False)

    async def asyncTearDown(self):
        await self.session.close()
        await self.engine.dispose()

    async def test_get_by_id_not_found(self):
        """get_by_id returns None when no event exists."""
        result = await ScheduledEvent.get_by_id(self.session, event_id=999)
        self.assertIsNone(result)

    async def test_get_by_id_found(self):
        """get_by_id returns the event after it is created."""
        event = ScheduledEvent(
            guild_id=1,
            channel_id=100,
            name="Jackbox",
            event_time=datetime.datetime(2026, 5, 1, 17, 0, 0),
            message_id=None,
        )
        self.session.add(event)
        await self.session.commit()

        result = await ScheduledEvent.get_by_id(self.session, event_id=event.id)
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "Jackbox")
        self.assertEqual(result.guild_id, 1)

    async def test_get_by_message_id(self):
        """get_by_message_id returns the event when message_id is set."""
        event = ScheduledEvent(
            guild_id=1,
            channel_id=100,
            name="Jackbox",
            event_time=datetime.datetime(2026, 5, 1, 17, 0, 0),
            message_id=999,
        )
        self.session.add(event)
        await self.session.commit()

        result = await ScheduledEvent.get_by_message_id(self.session, message_id=999)
        self.assertIsNotNone(result)
        self.assertEqual(result.name, "Jackbox")
        self.assertEqual(result.message_id, 999)

    async def test_get_by_message_id_not_found(self):
        """get_by_message_id returns None for an unknown message_id."""
        result = await ScheduledEvent.get_by_message_id(self.session, message_id=12345)
        self.assertIsNone(result)

    async def test_signup_created(self):
        """get_all_for_event returns the signup after creation."""
        event = ScheduledEvent(
            guild_id=1,
            channel_id=100,
            name="Jackbox",
            event_time=datetime.datetime(2026, 5, 1, 17, 0, 0),
            message_id=999,
        )
        self.session.add(event)
        await self.session.commit()

        signup = ScheduledEventSignup(event_id=event.id, user_id=42)
        self.session.add(signup)
        await self.session.commit()

        results = await ScheduledEventSignup.get_all_for_event(self.session, event_id=event.id)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].user_id, 42)

    async def test_signup_duplicate_raises(self):
        """Inserting a duplicate (event_id, user_id) signup raises IntegrityError."""
        event = ScheduledEvent(
            guild_id=1,
            channel_id=100,
            name="Jackbox",
            event_time=datetime.datetime(2026, 5, 1, 17, 0, 0),
            message_id=999,
        )
        self.session.add(event)
        await self.session.commit()

        signup1 = ScheduledEventSignup(event_id=event.id, user_id=42)
        self.session.add(signup1)
        await self.session.commit()

        signup2 = ScheduledEventSignup(event_id=event.id, user_id=42)
        self.session.add(signup2)
        with self.assertRaises(IntegrityError):
            await self.session.commit()


if __name__ == "__main__":
    unittest.main()
