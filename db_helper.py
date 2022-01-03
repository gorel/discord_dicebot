#!/usr/bin/env python3

import datetime
import sqlite3
import time
from typing import Any, Dict, Optional


STARTING_ROLL_VALUE = 6


ROLLS_TABLENAME = "rolls"
BANNED_MSG_TABLENAME = "banned_messages"
BANNED_PEOPLE_TABLENAME = "banned_people"

#########
# Rolls #
#########
ROLLS_SQL = """
CREATE TABLE IF NOT EXISTS {identifier} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    discord_id INTEGER NOT NULL,
    actual_roll INTEGER NOT NULL,
    target_roll INTEGER NOT NULL,
    date TEXT NOT NULL,
    rename_used INTEGER DEFAULT 0
);
"""


INSERT_ROLLS_SQL = """
INSERT INTO {identifier} (
    guild_id, discord_id, actual_roll, target_roll, date, rename_used)
    VALUES (?, ?, ?, ?, ?, ?);
"""


UPDATE_RENAME_USED_SQL = """
UPDATE {identifier}
SET rename_used = 1
WHERE guild_id = ?
  AND discord_id = ?
  AND actual_roll = {roll_target}
  AND target_roll = ?
"""


SELECT_LAST_WINNER_LOSER_SQL = """
SELECT
    discord_id,
    target_roll,
    rename_used
FROM {identifier}
WHERE guild_id = ?
  AND actual_roll = {roll_target}
ORDER BY id DESC
LIMIT 1
"""


SELECT_LAST_ROLL_TIME_SQL = """
SELECT
    date
FROM {identifier}
WHERE guild_id = ?
  AND discord_id = ?
ORDER BY date DESC
LIMIT 1
"""


SELECT_ALL_AGGREGATED_SQL = """
SELECT
    discord_id,
    SUM(CASE WHEN actual_roll = target_roll THEN 1 ELSE 0 END) AS wins,
    SUM(CASE WHEN actual_roll = 1 THEN 1 ELSE 0 END) AS losses,
    COUNT(1) AS cnt
FROM {identifier}
WHERE guild_id = ?
GROUP BY discord_id
"""


###################
# Banned messages #
###################
BANNED_MESSAGES_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS {identifier} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    msg_id INTEGER NOT NULL,
    unixtime INTEGER NOT NULL
);
"""


INSERT_BANNED_MSG_SQL = """
INSERT INTO {identifier} (guild_id, msg_id, unixtime)
    VALUES (?, ?, ?);
"""


SELECT_BANNED_MSG_SQL = """
SELECT
    id, guild_id, msg_id, unixtime
FROM {identifier}
WHERE guild_id = ?
  AND msg_id = ?
"""

#################
# Banned people #
#################
BANNED_PEOPLE_CREATE_SQL = """
CREATE TABLE IF NOT EXISTS {identifier} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    banner_discord_id INTEGER NOT NULL,
    bannee_discord_id INTEGER NOT NULL
);
"""

INSERT_BANNED_PERSON_SQL = """
INSERT INTO {identifier} (guild_id, banner_discord_id, bannee_discord_id)
    VALUES (?, ?, ?);
"""

SELECT_BANNED_LEADERBOARD_SQL = """
SELECT
    bannee_discord_id,
    COUNT(1) AS ban_count
FROM {identifier}
WHERE guild_id = ?
GROUP BY bannee_discord_id
"""

##############
# Delete SQL #
##############
DELETE_ALL_SQL = """
DELETE FROM {identifier}
WHERE guild_id = ?
"""


def db_connect(db_filename: str) -> sqlite3.Connection:
    return sqlite3.connect(db_filename)


def create_all(conn: sqlite3.Connection) -> None:
    # Create the rolls table
    sql = ROLLS_SQL.format(identifier=ROLLS_TABLENAME)
    cur = conn.cursor()
    cur.execute(sql)
    # Create the banned messages table
    sql = BANNED_MESSAGES_CREATE_SQL.format(identifier=BANNED_MSG_TABLENAME)
    cur.execute(sql)
    # Create the banned people table
    sql = BANNED_PEOPLE_CREATE_SQL.format(identifier=BANNED_PEOPLE_TABLENAME)
    cur.execute(sql)
    conn.commit()


def clear_all(conn: sqlite3.Connection, guild_id: int) -> None:
    for tbl in [ROLLS_TABLENAME, BANNED_MSG_TABLENAME, BANNED_PEOPLE_TABLENAME]:
        sql = DELETE_ALL_SQL.format(identifier=tbl)
        cur = conn.cursor()
        cur.execute(sql, (guild_id,))
    conn.commit()


def record_roll(
    conn: sqlite3.Connection, guild_id, discord_id, actual_roll, target_roll
) -> None:
    now = datetime.datetime.now()
    sql = INSERT_ROLLS_SQL.format(identifier=ROLLS_TABLENAME)
    cur = conn.cursor()
    cur.execute(sql, (guild_id, discord_id, actual_roll, target_roll, now, 0))
    conn.commit()


def record_rename_used_winner(
    conn: sqlite3.Connection, guild_id: int, discord_id: int, roll: int
) -> None:
    sql = UPDATE_RENAME_USED_SQL.format(
        identifier=ROLLS_TABLENAME, roll_target="target_roll"
    )
    cur = conn.cursor()
    cur.execute(sql, (guild_id, discord_id, roll))
    conn.commit()


def record_rename_used_loser(
    conn: sqlite3.Connection, guild_id: int, discord_id: int, roll: int
) -> None:
    sql = UPDATE_RENAME_USED_SQL.format(identifier=ROLLS_TABLENAME, roll_target="1")
    cur = conn.cursor()
    cur.execute(sql, (guild_id, discord_id, roll))
    conn.commit()


def get_last_roll_time(
    conn: sqlite3.Connection, guild_id: int, discord_id: int
) -> Optional[str]:
    sql = SELECT_LAST_ROLL_TIME_SQL.format(identifier=ROLLS_TABLENAME)
    cur = conn.cursor()
    cur.execute(sql, (guild_id, discord_id))
    try:
        row = cur.fetchone()
        return datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S.%f")
    except Exception:
        # It may be the case that this user has never rolled before
        return None


# TODO: Load into a real model
def get_all_stats(conn: sqlite3.Connection, guild_id: int) -> Dict[str, Any]:
    sql = SELECT_ALL_AGGREGATED_SQL.format(identifier=ROLLS_TABLENAME)
    cur = conn.cursor()
    cur.execute(sql, (guild_id,))
    return [
        {"discord_id": row[0], "wins": row[1], "losses": row[2], "attempts": row[3]}
        for row in cur.fetchall()
    ]


# TODO: Load into a real model
def get_last_winner(conn: sqlite3.Connection, guild_id: int) -> Dict[str, Any]:
    sql = SELECT_LAST_WINNER_LOSER_SQL.format(
        identifier=ROLLS_TABLENAME, roll_target="target_roll"
    )
    cur = conn.cursor()
    cur.execute(sql, (guild_id,))
    row = cur.fetchone()
    discord_id, roll, rename_used = None, None, None
    if row is not None:
        discord_id, roll, rename_used = row
    return {"discord_id": discord_id, "roll": roll, "rename_used": rename_used}


def get_last_loser(conn: sqlite3.Connection, guild_id: int) -> Dict[str, Any]:
    sql = SELECT_LAST_WINNER_LOSER_SQL.format(
        identifier=ROLLS_TABLENAME, roll_target="target_roll - 1"
    )
    cur = conn.cursor()
    cur.execute(sql, (guild_id,))
    row = cur.fetchone()
    discord_id, roll, rename_used = None, None, None
    if row is not None:
        discord_id, roll, rename_used = row
    return {"discord_id": discord_id, "roll": roll, "rename_used": rename_used}


def record_banned_message(conn: sqlite3.Connection, guild_id: int, msg_id: int) -> None:
    sql = INSERT_BANNED_MSG_SQL.format(identifier=BANNED_MSG_TABLENAME)
    cur = conn.cursor()
    cur.execute(sql, (guild_id, msg_id, int(time.time())))
    conn.commit()


def has_message_been_banned(
    conn: sqlite3.Connection, guild_id: int, msg_id: int
) -> bool:
    sql = SELECT_BANNED_MSG_SQL.format(identifier=BANNED_MSG_TABLENAME)
    cur = conn.cursor()
    cur.execute(sql, (guild_id, msg_id))
    return cur.fetchone() is not None


def record_banned_person(
    conn: sqlite3.Connection,
    guild_id: int,
    banner_discord_id: int,
    bannee_discord_id: int,
) -> None:
    sql = INSERT_BANNED_PERSON_SQL.format(identifier=BANNED_PEOPLE_TABLENAME)
    cur = conn.cursor()
    cur.execute(sql, (guild_id, banner_discord_id, bannee_discord_id))
    conn.commit()


def get_ban_stats(conn: sqlite3.Connection, guild_id: int):
    sql = SELECT_BANNED_LEADERBOARD_SQL.format(identifier=BANNED_PEOPLE_TABLENAME)
    cur = conn.cursor()
    cur.execute(sql, (guild_id,))
    return [{"discord_id": row[0], "ban_count": row[1]} for row in cur.fetchall()]
