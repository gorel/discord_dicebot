#!/usr/bin/env python3

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class HelpContext:
    name: str
    args: List[str]
    types: Dict[str, Any]
    usage: str

    def args_html(self) -> str:
        human_typenames = {
            "GreedyStr": "word, sentence, or phrase (spaces allowed)",
            "User": "@mention",
            "Time": "time (like '1hr', '8:59pm', 'Friday@8:59pm', or 'May30@12am')",
            "SetMessageSubcommand": "literal string 'win' or 'lose'",
            "int": "number",
            "str": "string (no spaces allowed)",
        }
        typenames = {arg: self.types[arg].__name__ for arg in self.args}
        simplified_typenames = {
            arg: human_typenames.get(t, t) for arg, t in typenames.items()
        }
        list_items = "".join(
            f"<li><code>{arg}: {simplified_typenames[arg]}</code></li>"
            for arg in self.args
        )
        return f"<ul>{list_items}</ul>"

    def __str__(self) -> str:
        # If there are args, we prepend a space character since it will
        # start right after the function name (otherwise there's a somewhat
        # awkward extra space with helptext for param-less functions)
        args_str = ""
        if len(self.args) > 0:
            args_str = " "
        # This is going to look like some more witchcraft, but we have to fully
        # instantiate a generic and then check its __class__ attribute since
        # calling issubclass immediately tells us that types[arg] is not a class
        args_str += " ".join(f"<{arg}>" for arg in self.args)
        if len(self.usage) > 0:
            usage = f": {self.usage}"
        else:
            usage = self.usage

        return f"__!{self.name}__{args_str}{usage}"
