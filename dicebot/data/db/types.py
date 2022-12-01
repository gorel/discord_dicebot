#!/usr/bin/env python3

from __future__ import annotations

import datetime
from typing import Annotated

from sqlalchemy import func
from sqlalchemy.orm import mapped_column

# Special types to make the ORM models prettier
int_pk = Annotated[int, mapped_column(primary_key=True)]
int_pk_natural = Annotated[int, mapped_column(primary_key=True, autoincrement=False)]
int_ix = Annotated[int, mapped_column(index=True)]
timestamp_now = Annotated[
    datetime.datetime,
    mapped_column(nullable=False, server_default=func.CURRENT_TIMESTAMP()),
]
bool_f = Annotated[bool, mapped_column(default=False)]
