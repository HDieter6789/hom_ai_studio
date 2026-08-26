FROM python:3.11-slim

WORKDIR /srv

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl postgresql-client \
    && rm -rf /var/lib/apt/lists/*

COPY packages/hom_core /srv/packages/hom_core
COPY apps/api/requirements.txt /srv/apps/api/requirements.txt

WORKDIR /srv/apps/api
RUN pip install --no-cache-dir -r requirements.txt

COPY apps/api /srv/apps/api
COPY infrastructure/scripts /srv/scripts
RUN chmod +x /srv/scripts/*.sh

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

ENTRYPOINT ["/srv/scripts/entrypoint-api.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
