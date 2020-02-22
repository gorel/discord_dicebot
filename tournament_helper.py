import json
import os
import random

from typing import List


TOURNAMENT_DATA_JSON = "tournament_data.json"


def _init():
    if not os.path.exists(TOURNAMENT_DATA_JSON):
        with open(TOURNAMENT_DATA_JSON, "w") as f:
            f.write("{}")


def help_message() -> str:
    msg = "Tournament usage:"
    msg += "\n - !tournament new <team_size>: create a new tournament (admin only)"
    msg += "\n - !tournament join: join the current tournament"
    msg += "\n - !tournament start: Make teams and start the tournament (admin only)"
    return msg


def new_tournament(guild_id: int, team_size: int) -> None:
    data = {
        "team_size": team_size,
        "players": [],
    }
    with open(TOURNAMENT_DATA_JSON) as f:
        tournament_data = json.load(f)

    tournament_data[str(guild_id)] = data
    with open(TOURNAMENT_DATA_JSON, "w") as f:
        json.dump(tournament_data, f)


def join_tournament(guild_id: int, discord_id: int) -> None:
    # TODO: Should probably return success or failure
    with open(TOURNAMENT_DATA_JSON) as f:
        tournament_data = json.load(f)
    players = tournament_data[str(guild_id)]["players"]
    if discord_id not in players:
        players.append(discord_id)
    with open(TOURNAMENT_DATA_JSON, "w") as f:
        json.dump(tournament_data, f)


def start_tournament(guild_id: int) -> List[List[int]]:
    with open(TOURNAMENT_DATA_JSON) as f:
        tournament_data = json.load(f)
    players = tournament_data[str(guild_id)]["players"]
    team_size = int(tournament_data[str(guild_id)]["team_size"])

    random.shuffle(players)
    teams: List[List[int]] = []
    for i in range(0, len(players), team_size):
        # TODO: If a team can't be filled properly, add bots or something
        next_team = players[i : i + team_size]
        teams.append(next_team)
    return teams


_init()
