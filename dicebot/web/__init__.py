#!/usr/bin/env python3

import os
import sys

import dotenv
import quart
import stytch

# Load environment
dotenv.load_dotenv()
QUART_DEBUG = bool(int(os.getenv("QUART_DEBUG", 0)))

# Load the Stytch credentials, but quit if they aren't defined
__stytch_project_id = os.getenv("STYTCH_PROJECT_ID")
__stytch_secret = os.getenv("STYTCH_SECRET")
__stytch_environment = os.getenv("STYTCH_ENVIRONMENT", "test")
if __stytch_project_id is None:
    sys.exit("STYTCH_PROJECT_ID env variable must be set before running")
if __stytch_secret is None:
    sys.exit("STYTCH_SECRET env variable must be set before running")

# Load the web secret key, used to sign sessions
__web_secret_key = os.getenv("WEB_SECRET_KEY")
if __web_secret_key is None:
    sys.exit("WEB_SECRET_KEY env variable must be defined to enable session signing")

# Create the web app and stytch client
quart_app = quart.Quart("dicebot.web")
quart_app.secret_key = __web_secret_key
stytch_client = stytch.Client(
    __stytch_project_id, __stytch_secret, environment=__stytch_environment
)
