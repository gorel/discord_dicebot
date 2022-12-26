#!/usr/bin/env python3

from __future__ import annotations

import datetime
from typing import Annotated

from sqlalchemy import BigInteger, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column

from dicebot.data.db.base import Base

# Special types to make the ORM models prettier
bigint_pk = Annotated[int, mapped_column(BigInteger, primary_key=True)]
bigint_ix = Annotated[int, mapped_column(BigInteger, index=True)]
timestamp_now = Annotated[
    datetime.datetime,
    mapped_column(nullable=False, server_default=func.CURRENT_TIMESTAMP()),
]


class Thanks(Base):
    __tablename__ = "thanks"

    # Columns
    id: Mapped[bigint_pk]
    guild_id: Mapped[bigint_ix] = mapped_column(ForeignKey("guild.id"))
    thanker_id: Mapped[bigint_ix] = mapped_column(ForeignKey("discord_user.id"))
    thankee_id: Mapped[bigint_ix] = mapped_column(ForeignKey("discord_user.id"))
    reason: Mapped[str]
    created_at: Mapped[timestamp_now]
