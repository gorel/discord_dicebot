FROM python:3.10

ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y \
  # Clean up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

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

WORKDIR /app

ENTRYPOINT ["/entrypoint"]

