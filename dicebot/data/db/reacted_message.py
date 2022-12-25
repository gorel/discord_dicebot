#!/usr/bin/env python3

from __future__ import annotations

import datetime
from typing import Annotated, Optional

from sqlalchemy import BigInteger, ForeignKey, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from dicebot.data.db.base import Base

# Special types to make the ORM models prettier
bigint = Annotated[int, mapped_column(BigInteger)]
bigint_pk = Annotated[int, mapped_column(BigInteger, primary_key=True)]
bigint_ix = Annotated[int, mapped_column(BigInteger, index=True)]
timestamp_now = Annotated[
    datetime.datetime,
    mapped_column(nullable=False, server_default=func.CURRENT_TIMESTAMP()),
]


class ReactedMessage(Base):
    __tablename__ = "reacted_message"

    # Columns
    id: Mapped[bigint_pk]
    guild_id: Mapped[bigint_ix] = mapped_column(ForeignKey("guild.id"))
    msg_id: Mapped[bigint_ix]
    reacted_at: Mapped[timestamp_now]
    reaction_id: Mapped[bigint]

    # Methods
    @classmethod
    async def get_by_msg_and_reaction_id(
        cls, session: AsyncSession, msg_id: int, reaction_id: int
    ) -> Optional[ReactedMessage]:
        res = await session.scalars(
            select(cls).filter_by(msg_id=msg_id, reaction_id=reaction_id).limit(1)
        )
        return res.one_or_none()

    def __repr__(self) -> str:
        return (
            f"ReactedMessage({self.id=}, {self.guild_id=}, "
            f"{self.msg_id=}, {self.reacted_at=}, {self.reaction_id=})"
        )
