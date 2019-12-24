import datetime

import sqlite3


STARTING_ROLL_VALUE = 6


WINNERS_TABLENAME = "winners"
LOSERS_TABLENAME = "losers"


WINNER_LOSER_SQL = """
CREATE TABLE IF NOT EXISTS {identifier} (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    guild_id INTEGER NOT NULL,
    discord_id INTEGER NOT NULL,
    roll INTEGER NOT NULL,
    date TEXT NOT NULL,
    rename_used INTEGER DEFAULT 0
);
"""


INSERT_WINNER_LOSER_SQL = """
INSERT INTO {identifier} (guild_id, discord_id, roll, date, rename_used)
    VALUES (?, ?, ?, ?, ?);
"""


UPDATE_RENAME_USED_SQL = """
UPDATE {identifier}
SET rename_used = 1
WHERE guild_id = ?
  AND discord_id = ?
  AND roll = ?
"""


SELECT_LAST_WINNER_LOSER_SQL = """
SELECT
    discord_id,
    roll,
    rename_used
FROM {identifier}
WHERE guild_id = ?
ORDER BY id DESC
LIMIT 1
"""


SELECT_ALL_AGGREGATED_SQL = """
SELECT
    discord_id,
    COUNT(1) AS cnt
FROM {identifier}
WHERE guild_id = ?
GROUP BY discord_id
ORDER BY 2 DESC
"""


def db_connect(db_filename):
    return sqlite3.connect(db_filename)

def create_winners_table(conn):
    sql = WINNER_LOSER_SQL.format(identifier=WINNERS_TABLENAME)
    cur = conn.cursor()
    cur.execute(sql)


def create_losers_table(conn):
    sql = WINNER_LOSER_SQL.format(identifier=LOSERS_TABLENAME)
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()


def create_all(conn):
    create_winners_table(conn)
    create_losers_table(conn)


def get_next_roll(conn, guild_id):
    sql = """
    SELECT MAX(roll)
    FROM winners
    WHERE guild_id = ?
    """
    cur = conn.cursor()
    cur.execute(sql, (guild_id, ))
    row = cur.fetchone()
    if row is None or row[0] is None:
        return STARTING_ROLL_VALUE
    return row[0] + 1


def add_winner(conn, guild_id, discord_id, roll):
    now = datetime.datetime.now()
    sql = INSERT_WINNER_LOSER_SQL.format(identifier=WINNERS_TABLENAME)
    cur = conn.cursor()
    cur.execute(sql, (guild_id, discord_id, roll, now, 0))
    conn.commit()


def add_loser(conn, guild_id, discord_id, roll):
    now = datetime.datetime.now()
    sql = INSERT_WINNER_LOSER_SQL.format(identifier=LOSERS_TABLENAME)
    cur = conn.cursor()
    cur.execute(sql, (guild_id, discord_id, roll, now, 0))
    conn.commit()


def record_rename_used_winner(conn, guild_id, discord_id, roll):
    sql = UPDATE_RENAME_USED_SQL.format(identifier=WINNERS_TABLENAME)
    cur = conn.cursor()
    cur.execute(sql, (guild_id, discord_id, roll))
    conn.commit()


def record_rename_used_loser(conn, guild_id, discord_id, roll):
    sql = UPDATE_RENAME_USED_SQL.format(identifier=LOSERS_TABLENAME)
    cur = conn.cursor()
    cur.execute(sql, (guild_id, discord_id, roll))
    conn.commit()


def get_all_winners(conn, guild_id):
    sql = SELECT_ALL_AGGREGATED_SQL.format(identifier=WINNERS_TABLENAME)
    cur = conn.cursor()
    cur.execute(sql, (guild_id, ))
    return [
        {"discord_id": row[0], "count": row[1]} for row in cur.fetchall()
    ]


def get_all_losers(conn, guild_id):
    sql = SELECT_ALL_AGGREGATED_SQL.format(identifier=LOSERS_TABLENAME)
    cur = conn.cursor()
    cur.execute(sql, (guild_id, ))
    return [
        {"discord_id": row[0], "count": row[1]} for row in cur.fetchall()
    ]


def get_last_winner(conn, guild_id):
    sql = SELECT_LAST_WINNER_LOSER_SQL.format(identifier=WINNERS_TABLENAME)
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
    sql = SELECT_LAST_WINNER_LOSER_SQL.format(identifier=LOSERS_TABLENAME)
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
