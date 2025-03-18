FROM mcr.microsoft.com/devcontainers/python:3.12

ENV PYTHONUNBUFFERED=1

# Pillow dependencies
RUN apt-get update \
  && apt-get install -y \
  libffi8 \
  libgdk-pixbuf2.0-0 \
  liblcms2-2 \
  libopenjp2-7 \
  libssl3 \
  libtiff6 \
  libwebp7 \
  libpq5 \
  shared-mime-info \
  mime-support \
  pipx

RUN pipx ensurepath

WORKDIR /app
RUN pipx install poetry==2.1.1
RUN poetry config virtualenvs.create false
COPY poetry.lock pyproject.toml /app/
RUN poetry sync
