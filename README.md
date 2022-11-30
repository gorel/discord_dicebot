# Discord Dicebot

A dicebot that has gradually accumulated features over the years. At this point, rolling dice is a minor feature compared
to the other commands and handlers it has in place.

Setup:

```
python3.10 -m venv venv
source venv/bin/activate
pip install -r pip_requirements.txt
```

Usage:

```
usage: main.py [-h] [-t] [-e ENV_FILE]

options:
  -h, --help            show this help message and exit
  -t, --test            Start the bot in test mode
  -e ENV_FILE, --env-file ENV_FILE
                        Use a specific file for dotenv (defaults to .env)
```

Environment settings (put these in your `.env` file)

- `DISCORD_TOKEN`: your [Discord bot token](https://discord.com/developers/docs/topics/oauth2)
- `TENOR_API_KEY`: a key for [tenor](https://tenor.com/gifapi/documentation)
- `GITHUB_USER`: Username for the GitHub account to use `!fileatask`
- `GITHUB_PASS`: Password for the GitHub account to use `!fileatask`
- `OWNER_DISCORD_ID`: The Discord ID of the owner (used for `!fileatask`)
- `TEST_GUILD_ID`: If set and the bot starts in test mode, it will ignore any other guilds
