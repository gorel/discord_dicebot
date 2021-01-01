import datetime

import sqlite3


STARTING_ROLL_VALUE = 6


TABLENAME = "rolls"


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


SELECT_ALL_AGGREGATED_SQL = """
SELECT
    discord_id,
    COUNT_IF(actual_roll = target_roll) AS wins,
    COUNT_IF(actual_roll = 1) AS losses,
    COUNT(1) AS cnt
FROM {identifier}
WHERE guild_id = ?
GROUP BY discord_id
ORDER BY 2 DESC
"""


DELETE_ALL_SQL = """
DELETE FROM {identifier}
WHERE guild_id = ?
"""


def db_connect(db_filename):
    return sqlite3.connect(db_filename)


def create_all(conn):
    sql = ROLLS_SQL.format(identifier=TABLENAME)
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()


def clear_all(conn, guild_id):
    sql = DELETE_ALL_SQL.format(identifier=TABLENAME)
    cur = conn.cursor()
    cur.execute(sql, (guild_id, ))
    conn.commit()


def record_roll(conn, guild_id, discord_id, actual_roll, target_roll):
    now = datetime.datetime.now()
    sql = INSERT_ROLLS_SQL.format(identifier=TABLENAME)
    cur = conn.cursor()
    cur.execute(sql, (guild_id, discord_id, actual_roll, target_roll, now, 0))


def record_rename_used_winner(conn, guild_id, discord_id, roll):
    sql = UPDATE_RENAME_USED_SQL.format(
        identifier=TABLENAME,
        roll_target="target_roll",
    )
    cur = conn.cursor()
    cur.execute(sql, (guild_id, discord_id, roll))
    conn.commit()


def record_rename_used_loser(conn, guild_id, discord_id, roll):
    sql = UPDATE_RENAME_USED_SQL.format(
        identifier=TABLENAME,
        roll_target="1",
    )
    cur = conn.cursor()
    cur.execute(sql, (guild_id, discord_id, roll))
    conn.commit()


def get_all_stats(conn, guild_id):
    sql = SELECT_ALL_AGGREGATED_SQL.format(identifier=TABLENAME)
    cur = conn.cursor()
    cur.execute(sql, (guild_id, ))
    return [
        {"discord_id": row[0], "wins": row[1], "losses": row[2], "attempts": row[3]}
        for row in cur.fetchall()
    ]


def get_last_winner(conn, guild_id):
    sql = SELECT_LAST_WINNER_LOSER_SQL.format(
        identifier=TABLENAME,
        roll_target="target_roll",
    )
    cur = conn.cursor()
    cur.execute(sql, (guild_id, ))
    row = cur.fetchone()
    discord_id, roll, rename_used = None, None, None
    if row is not None:
        discord_id, roll, rename_used = row
    return {
        "discord_id": discord_id,
        "roll": roll,
        "rename_used": rename_used,
    }


def get_last_loser(conn, guild_id):
    sql = SELECT_LAST_WINNER_LOSER_SQL.format(
        identifier=TABLENAME,
        roll_target="1",
    )
    cur = conn.cursor()
    cur.execute(sql, (guild_id, ))
    row = cur.fetchone()
    discord_id, roll, rename_used = None, None, None
    if row is not None:
        discord_id, roll, rename_used = row
    return {
        "discord_id": discord_id,
        "roll": roll,
        "rename_used": rename_used,
    }
