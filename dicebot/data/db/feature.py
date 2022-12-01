#!/usr/bin/env python3

from __future__ import annotations

from typing import Annotated

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column

from dicebot.data.db.base import Base

# Special types to make the ORM models prettier
int_pk = Annotated[int, mapped_column(primary_key=True)]


class Feature(Base):
    # TODO: Use enums to define features and load them on setup/create_all
    __tablename__ = "feature"

    # Columns
    id: Mapped[int_pk]
    feature_name: Mapped[str]

    # Methods
    @classmethod
    async def get_or_create(cls, session: AsyncSession, feature_name: str) -> Feature:
        query = await session.scalars(select(cls).filter_by(feature_name=feature_name))
        res = query.one_or_none()
        if res is None:
            res = cls(feature_name=feature_name)
            session.add(res)
            await session.commit()
        return res
