#!/usr/bin/env python3

from __future__ import annotations

import datetime
from typing import Annotated, Optional

from sqlalchemy import ForeignKey, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from dicebot.data.db.base import Base

# Special types to make the ORM models prettier
int_pk = Annotated[int, mapped_column(primary_key=True)]
int_ix = Annotated[int, mapped_column(index=True)]
timestamp_now = Annotated[
    datetime.datetime,
    mapped_column(nullable=False, server_default=func.CURRENT_TIMESTAMP()),
]


class ReactedMessage(Base):
    __tablename__ = "reacted_message"

    # Columns
    id: Mapped[int_pk]
    guild_id: Mapped[int_ix] = mapped_column(ForeignKey("guild.id"))
    msg_id: Mapped[int_ix]
    reacted_at: Mapped[timestamp_now]
    reaction_id: Mapped[int]

    # Methods
    @classmethod
    async def get_by_msg_and_reaction_id(
        cls, session: AsyncSession, msg_id: int, reaction_id: int
    ) -> Optional[ReactedMessage]:
        res = await session.scalars(
            select(cls).filter_by(msg_id=msg_id, reaction_id=reaction_id)
        )
        return res.one_or_none()
