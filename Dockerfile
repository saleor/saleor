### Build and install packages
FROM python:3.12 AS build-python

RUN apt-get -y update \
  && apt-get install -y gettext \
  # Cleanup apt cache
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
WORKDIR /app
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_SYSTEM_PYTHON=1 UV_PROJECT_ENVIRONMENT=/usr/local
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

### Final image
FROM python:3.12-slim

RUN groupadd -r saleor && useradd -r -g saleor saleor

# Pillow dependencies
RUN apt-get update \
  && apt-get install -y \
  libffi8 \
  libgdk-pixbuf-2.0-0 \
  liblcms2-2 \
  libopenjp2-7 \
  libssl3 \
  libtiff6 \
  libwebp7 \
  libpq5 \
  libmagic1 \
  # Required by celery[sqs] which uses pycurl for AWS SQS support
  libcurl4 \
  # Required to allows to identify file types when handling file uploads
  media-types \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /app/media /app/static \
  && chown -R saleor:saleor /app/

COPY --from=build-python /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/
COPY --from=build-python /usr/local/bin/ /usr/local/bin/
COPY . /app
WORKDIR /app

ARG STATIC_URL
ENV STATIC_URL=${STATIC_URL:-/static/}
RUN SECRET_KEY=dummy STATIC_URL=${STATIC_URL} python3 manage.py collectstatic --no-input

EXPOSE 8000
ENV PYTHONUNBUFFERED=1

LABEL org.opencontainers.image.title="saleor/saleor" \
  org.opencontainers.image.description="The commerce engine for modern software development teams." \
  org.opencontainers.image.url="https://saleor.io/" \
  org.opencontainers.image.source="https://github.com/saleor/saleor" \
  org.opencontainers.image.authors="Saleor Commerce (https://saleor.io)" \
  org.opencontainers.image.licenses="BSD-3-Clause"

CMD ["uvicorn", "saleor.asgi:application", "--host=0.0.0.0", "--port=8000", "--workers=2", "--lifespan=off", "--ws=none", "--no-server-header", "--no-access-log", "--timeout-keep-alive=35", "--timeout-graceful-shutdown=30", "--limit-max-requests=10000"]
