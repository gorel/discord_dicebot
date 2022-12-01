# Discord Dicebot

A dicebot that has gradually accumulated features over the years. At this point, rolling dice is a minor feature compared
to the other commands and handlers it has in place.

Setup:

```
# venv is optional but highly encouraged
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Usage:

```
# From project root directory
$ python -m dicebot.app.bot
```

Environment settings (put these in your `.env` file)

- `DISCORD_TOKEN`: Your [Discord bot token](https://discord.com/developers/docs/topics/oauth2)
- `TENOR_API_KEY`: A key for [tenor](https://tenor.com/gifapi/documentation)
- `GITHUB_USER`: Username for the GitHub account to use `!fileatask`
- `GITHUB_PASS`: Password for the GitHub account to use `!fileatask`
- `OWNER_DISCORD_ID`: The Discord ID of the owner (used for `!fileatask`)
- `TEST_GUILD_ID`: If set, it will ignore any other guilds
- `CELERY_BROKER_URL`: The broker Celery will use to send/receive messages
- `CELERY_RESULT_BACKEND`: The backend Celery will use to persist results
