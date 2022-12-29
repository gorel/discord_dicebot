# Discord Dicebot

A dicebot that has gradually accumulated features over the years. At this point, rolling dice is a minor feature compared
to the other commands and handlers it has in place.

Setup:

```
# venv is optional but highly encouraged
python3.10 -m venv .venv
source .venv/bin/activate
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

## Running the IPython shell

You can run an interactive Python shell where you can use the client directly like so:

```
# From project root directory
$ python -m dicebot.app.ipython
```

By default, you'll have access to `prep` which is a function that allows calling `async` functions in a synchronous context (behind the scenes, it's getting the `asyncio` event loop and calls `loop.run_until_complete`) as well as `client` which is the logged in `dicebot.core.client.Client` object.

```
[1] prep(Client.fetch_guild(MY_GUILD_ID))
```

## Using docker compose

This section is rather sparse because I don't fully know what I'm doing.
As a result, I'll document what I can here below, but there are no promises on the quality of the content.

### For debugging

To run all services locally for debugging:

```
$ docker compose up
```

To run the webserver without other services:

```
$ docker compose run --service-ports web
```

### DB without other services

If you want to run the db _without_ starting other services:

```
$ docker compose run db
$ docker compose exec db /bin/bash
# Inside the container -- assumes username of dicebot
$ psql -U dicebot
```

**NOTE**: You can add more volumes when running `docker compose run` which can be useful to link
something like `$(realpath migration.sql):/migration.sql` to later run raw SQL through Postgres.
This was useful when first starting the new bot since I created the migration data from SQLite
and ran `cat migration.sql | psql -1 -U dicebot`

### Setting up for automation

To run all services automatically as part of a daemonization job

```
$ ./setup-service.sh
```

You'll now have a new `systemctl` service called `docker-compose@dicebot`.
To check the status, type `systemctl status docker-compose@dicebot`.

Edit the `/etc/sudoers.d/$USER` file and include the following (replace $VARIABLES with real values):

```
%$USER ALL= NOPASSWD: /bin/systemctl start docker-compose@dicebot
%$USER ALL= NOPASSWD: /bin/systemctl stop docker-compose@dicebot
%$USER ALL= NOPASSWD: /bin/systemctl restart docker-compose@dicebot
```

From there, check out the `.github/workflows/deploy.yml` workflow to see how it works to automatically restart the
service on the remote machine where `dicebot` is running.
