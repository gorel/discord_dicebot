#!/usr/bin/env python3

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Optional, Sequence

from discord import Reaction
from sqlalchemy import BigInteger, ForeignKey, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Mapped, mapped_column, relationship

from dicebot.data.db.base import Base

if TYPE_CHECKING:
    from dicebot.data.db.guild import Guild
    from dicebot.data.db.user import User

# Special types to make the ORM models prettier
int_pk = Annotated[int, mapped_column(BigInteger, primary_key=True)]
int_ix = Annotated[int, mapped_column(BigInteger, index=True)]


class CustomReactionHandler(Base):
    __tablename__ = "custom_reaction_handler"

    # Columns
    id: Mapped[int_pk]
    guild_id: Mapped[int_ix] = mapped_column(ForeignKey("guild.id"))
    added_by: Mapped[int_ix] = mapped_column(ForeignKey("discord_user.id"))
    reaction_id: Mapped[int_ix]
    reaction_name: Mapped[str]
    gif_search: Mapped[str]

    # Relationships
    author: Mapped[User] = relationship("User", lazy="selectin")

    def reaction_equal(self, reaction: Reaction) -> bool:
        emoji = reaction.emoji
        if isinstance(emoji, str):
            return False

        return emoji.id == self.reaction_id and emoji.name == self.reaction_name

    @classmethod
    async def get(
        cls, session: AsyncSession, guild: Guild, reaction_id: int, reaction_name: str
    ) -> Optional[CustomReactionHandler]:
        res = await session.scalars(
            select(CustomReactionHandler)
            .filter_by(
                guild_id=guild.id, reaction_id=reaction_id, reaction_name=reaction_name
            )
            .limit(1)
        )
        return res.one_or_none()

    @classmethod
    async def get_all(
        cls, session: AsyncSession, guild: Guild
    ) -> Sequence[CustomReactionHandler]:
        res = await session.scalars(
            select(CustomReactionHandler).filter_by(guild_id=guild.id)
        )
        return res.all()

    def __repr__(self) -> str:
        return (
            f"CustomReactionHandler({self.id=}, {self.reaction=}, {self.gif_search=})"
        )
