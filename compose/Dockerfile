FROM python:3.11

ENV PYTHONUNBUFFERED 1

# Install requirements here to ensure they get cached
COPY requirements.txt /requirements.txt
RUN pip install --no-cache-dir -r /requirements.txt

COPY ./compose/entrypoint /entrypoint
RUN chmod +x /entrypoint

COPY ./compose/bot/start /start-bot
RUN chmod +x /start-bot

COPY ./compose/celery/worker/start /start-celeryworker
RUN chmod +x /start-celeryworker

COPY ./compose/celery/beat/start /start-celerybeat
RUN chmod +x /start-celerybeat

COPY ./compose/web/start /start-web
RUN chmod +x /start-web

WORKDIR /app

ENTRYPOINT ["/entrypoint"]

