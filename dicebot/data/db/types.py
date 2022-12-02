#!/usr/bin/env python3

from __future__ import annotations

import datetime
from typing import Annotated

from sqlalchemy import BigInteger, func
from sqlalchemy.orm import mapped_column

# Special types to make the ORM models prettier
bigint = Annotated[int, mapped_column(BigInteger)]
bigint_pk = Annotated[int, mapped_column(BigInteger, primary_key=True)]
bigint_pk_natural = Annotated[
    int, mapped_column(BigInteger, primary_key=True, autoincrement=False)
]
bigint_ix = Annotated[int, mapped_column(BigInteger, index=True)]
timestamp_now = Annotated[
    datetime.datetime,
    mapped_column(nullable=False, server_default=func.CURRENT_TIMESTAMP()),
]
bool_f = Annotated[bool, mapped_column(default=False)]
