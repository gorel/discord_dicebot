#!/usr/bin/env python3

from dicebot.web import QUART_DEBUG, quart_app
from dicebot.web.middleware import register_middleware
from dicebot.web.routes import register_routes


def main() -> None:
    register_middleware()
    register_routes()
    quart_app.run(host="0.0.0.0", debug=QUART_DEBUG)


if __name__ == "__main__":
    main()
