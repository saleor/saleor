### Build and install packages
FROM python:3.9-bookworm as build-python

RUN apt-get -y update \
  && apt-get install -y gettext \
  # Cleanup apt cache
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
WORKDIR /app
RUN --mount=type=cache,mode=0755,target=/root/.cache/pip pip install poetry==1.7.0
RUN poetry config virtualenvs.create false
COPY poetry.lock pyproject.toml /app/
RUN --mount=type=cache,mode=0755,target=/root/.cache/pypoetry poetry install --no-root

### Final image
FROM python:3.9-slim-bookworm

RUN groupadd -r saleor && useradd -r -g saleor saleor

RUN apt-get update \
  && apt-get install -y \
  libcairo2 \
  libgdk-pixbuf2.0-0 \
  liblcms2-2 \
  libopenjp2-7 \
  libpango-1.0-0 \
  libpangocairo-1.0-0 \
  libssl3 \
  libtiff6 \
  libwebp7 \
  libxml2 \
  libpq5 \
  shared-mime-info \
  mime-support \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*

RUN echo 'image/webp webp' >> /etc/mime.types
RUN echo 'image/avif avif' >> /etc/mime.types

RUN mkdir -p /app/media /app/static \
  && chown -R saleor:saleor /app/

COPY --from=build-python /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
COPY --from=build-python /usr/local/bin/ /usr/local/bin/
COPY . /app
WORKDIR /app

ARG STATIC_URL
ENV STATIC_URL ${STATIC_URL:-/static/}
RUN SECRET_KEY=dummy STATIC_URL=${STATIC_URL} python3 manage.py collectstatic --no-input

EXPOSE 8000
ENV PYTHONUNBUFFERED 1

LABEL org.opencontainers.image.title="saleor/saleor"                                  \
      org.opencontainers.image.description="\
A modular, high performance, headless e-commerce platform built with Python, \
GraphQL, Django, and ReactJS."                                                         \
      org.opencontainers.image.url="https://saleor.io/"                                \
      org.opencontainers.image.source="https://github.com/saleor/saleor"               \
      org.opencontainers.image.authors="Saleor Commerce (https://saleor.io)"           \
      org.opencontainers.image.licenses="BSD 3"

CMD ["gunicorn", "--bind", ":8000", "--workers", "4", "--worker-class", "saleor.asgi.gunicorn_worker.UvicornWorker", "saleor.asgi:application"]
