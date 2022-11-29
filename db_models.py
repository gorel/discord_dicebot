#!/usr/bin/env python3

from __future__ import annotations

import datetime
from typing import Annotated, Optional

from sqlalchemy import Column, ForeignKey, Table, func
from sqlalchemy.orm import (Mapped, declarative_base, mapped_column,
                            relationship)

# Special types to make the ORM models below prettier
int_pk = Annotated[int, mapped_column(primary_key=True)]
timestamp = Annotated[
    datetime.datetime,
    mapped_column(nullable=False, server_default=func.CURRENT_TIMESTAMP()),
]

Base = declarative_base()

# Many-to-many assoc to link servers to features
server_feature_assoc = Table(
    "server_feature_assoc",
    Base.metadata,
    Column("server_id", ForeignKey("server.id")),
    Column("feature_id", ForeignKey("feature.id")),
)


class DiscordUser(Base):
    __tablename__ = "discord_user"
    id: Mapped[int_pk]
    discord_id: Mapped[int]
    birthday: Mapped[Optional[str]]


class Server(Base):
    __tablename__ = "server"
    id: Mapped[int_pk]
    guild_id: Mapped[int]
    current_roll: Mapped[int]
    roll_timeout: Mapped[int]
    critical_success_msg: Mapped[str]
    critical_failure_msg: Mapped[str]
    allow_renaming: Mapped[bool]
    enabled_features: Mapped[list[Feature]] = relationship(
        secondary=server_feature_assoc
    )


class Diceboss(Base):
    __tablename__ = "diceboss"
    id: Mapped[int_pk]
    server_id: Mapped[int_pk] = mapped_column(ForeignKey("server.id"))
    discord_user_id: Mapped[int_pk] = mapped_column(ForeignKey("discord_user.id"))


class Macro(Base):
    __tablename__ = "macro"
    id: Mapped[int_pk]
    server_id: Mapped[int_pk] = mapped_column(ForeignKey("server.id"))
    added_by: Mapped[int_pk] = mapped_column(ForeignKey("discord_user.id"))
    key: Mapped[str]
    value: Mapped[str]


class Roll(Base):
    __tablename__ = "roll"
    id: Mapped[int_pk]
    server_id: Mapped[int_pk] = mapped_column(ForeignKey("server.id"))
    discord_user_id: Mapped[int_pk] = mapped_column(ForeignKey("discord_user.id"))
    actual_roll: Mapped[int]
    target_roll: Mapped[int]
    rolled_at: Mapped[timestamp]


class Rename(Base):
    __tablename__ = "rename"
    id: Mapped[int_pk]
    server_id: Mapped[int_pk] = mapped_column(ForeignKey("server.id"))
    discord_user_id: Mapped[int_pk] = mapped_column(ForeignKey("discord_user.id"))
    rename_type: Mapped[int]
    rename_used: Mapped[bool]


class Feature(Base):
    __tablename__ = "feature"
    id: Mapped[int_pk]
    feature_name: Mapped[str]


class Ban(Base):
    __tablename__ = "ban"
    id: Mapped[int_pk]
    bannee_id: Mapped[int]
    banner_id: Mapped[int]
    reason: Mapped[str]
    banned_at: Mapped[timestamp]
    banned_until: Mapped[timestamp]
    voided: Mapped[bool]
