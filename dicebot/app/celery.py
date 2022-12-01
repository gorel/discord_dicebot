#!/usr/bin/env python3

from dicebot.app.common import celery_app

if __name__ == "__main__":
    # Just run the celery app
    celery_app.start()
