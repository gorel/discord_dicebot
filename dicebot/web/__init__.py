#!/usr/bin/env python3

import os
from dataclasses import dataclass

import dotenv
import quart
import stytch
from sqlalchemy.ext.asyncio import AsyncSession

from dicebot.core.client import Client

# Load environment
dotenv.load_dotenv()
QUART_DEBUG = bool(int(os.getenv("QUART_DEBUG", 0)))


# Load the web secret key, used to sign sessions
__web_secret_key = os.getenv("WEB_SECRET_KEY")

# Create the web app and stytch client
quart_app = quart.Quart("dicebot.web")
quart_app.secret_key = __web_secret_key

# Load the Stytch credentials
__stytch_project_id = os.getenv("STYTCH_PROJECT_ID", "")
__stytch_secret = os.getenv("STYTCH_SECRET", "")
__stytch_environment = os.getenv("STYTCH_ENVIRONMENT", "test")
stytch_client = stytch.Client(
    __stytch_project_id, __stytch_secret, environment=__stytch_environment
)


# Create the app_ctx for using globals created at startup
# This will be properly initialized in the {before|while}_serving middleware
@dataclass
class AppContext:
    discord_client: Client
    session: AsyncSession


app_ctx = AppContext(None, None)  # type: ignore
