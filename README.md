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

Environment settings (put these in your `.env` file). There's a sample file in the root of the repository called
`sample.env` that may be useful to reference. You should consider using a better `POSTGRES_PASSWORD` for the database,
but within `sample.env`, `dicebot_pw` is the password used to illustrate how to construct the `DATABASE_URL`.

There are three important API keys you will need to retrieve:

- `DISCORD_TOKEN`: Your [Discord bot token](https://discord.com/developers/docs/topics/oauth2)
- `TENOR_API_KEY`: A key for [tenor](https://tenor.com/gifapi/documentation)
- `OPENAI_API_KEY`: A key for [OpenAI](https://beta.openai.com/account/api-keys)

You must also replace the `DISCORD_OAUTH_LINK` with the OAuth link from Stytch and set up the OAuth2 redirect at
https://discord.com/developers/applications for the webserver to work for login.

## Running tests

Tests can be run with `make test`

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

### Web automation

DigitalOcean has [great tutorials on setting up
nginx](https://www.digitalocean.com/community/tutorials/how-to-install-nginx-on-ubuntu-18-04#step-5-%E2%80%93-setting-up-server-blocks-recommended).

Follow [the guide from here](https://www.uvicorn.org/deployment/#running-behind-nginx) to set up Hypercorn. Even though
that guide is for uvicorn, the setup is the same.
