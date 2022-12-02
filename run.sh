#!/bin/sh

# Start redis
redis-server --daemonize yes

# Start the celery background workers
celery multi start w1 -A dicebot -l INFO

# And run the bot
python -m dicebot.app.bot
