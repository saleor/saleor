FROM mcr.microsoft.com/devcontainers/python:3.12

ENV PYTHONUNBUFFERED=1

# Pillow dependencies
RUN apt-get update \
  && apt-get install -y \
  libffi8 \
  libgdk-pixbuf-2.0-0\
  liblcms2-2 \
  libopenjp2-7 \
  libssl3 \
  libtiff6 \
  libwebp7 \
  libpq5 \
  shared-mime-info \
  libmagic1 \
  # Required to allows to identify file types when handling file uploads
  media-types

COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /uvx /bin/
ENV UV_COMPILE_BYTECODE=1 UV_SYSTEM_PYTHON=1 UV_PROJECT_ENVIRONMENT=/usr/local
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable
