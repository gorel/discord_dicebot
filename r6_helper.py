import enum
import json

from typing import List


USER_DATA_JSON = "user_data.json"

R6_ATK = ["Sledge", "Thatcher", "Ash", "Thermite", "Mick", "Tick", "Blitz", "IQ", "Fuze", "Glaz", "Buck", "Blackbeard", "Capitao", "Hibana", "Jackal", "Ying", "Zofia", "Dokkaebi", "Finka", "Lion", "Maverick","Nomad", "Gridlock", "Spooky bitch atk", "Amaru", "Kali"]
R6_DEF = ["Mute", "Smonk", "Castle", "Pulse", "Dick", "Rick", "Jager", "Bandit", "God", "Kapkan", "Frost", "Valkyrie", "Spooky bitch def", "Echo", "Mira", "Lesion", "Ela", "Vigil", "Alibi", "Maestro", "Clash","Kaid", "Mozzie", "Warden", "Goyo", "Wamai"]


class OperatorSide(enum.Enum):
    ATTACK = 0
    DEFENSE = 1



def _get_valid_ops(side: OperatorSide, user_id: str) -> List[str]:
    with open(USER_DATA_JSON) as f:
        operators = json.load(f)

    if user_id not in operators:
        operators[user_id] = []

    with open(USER_DATA_JSON, "w") as f:
        json.dump(operators, f)

    if side == OperatorSide.ATTACK:
        possible_ops = R6_ATK
    else:
        possible_ops = R6_DEF
    return [op for op in operators[user_id] if op.title() in possible_ops]


def pick_attacker(user_id: int) -> str:
    ops = _get_valid_ops(OperatorSide.ATTACK, str(user_id))
    return random.choice(ops)


def pick_defender(user_id: int) -> str:
    ops = _get_valid_ops(OperatorSide.DEFENSE, str(user_id))
    return random.choice(ops)


def disable_operators(user_id: int, ops: List[str]) -> List[str]:
    user_str = str(user_id)
    with open(USER_DATA_JSON) as f:
        operators = json.load(f)
    disabled_ops = set(operators.get(user_str, [])) + set(ops)
    operators[user_str] = list(disabled_ops)

    with open(USER_DATA_JSON, "w") as f:
        json.dump(operators, f)
    return disabled_ops


def enable_operators(user_id: int, ops: List[str]) -> List[str]:
    user_str = str(user_id)
    with open(USER_DATA_JSON) as f:
        operators = json.load(f)
    disabled_ops = set(operators.get(user_str, [])) - set(ops)
    operators[user_str] = list(disabled_ops)

    with open(USER_DATA_JSON, "w") as f:
        json.dump(operators, f)
    return disabled_ops
