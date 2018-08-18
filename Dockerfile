### Build and install packages
FROM python:3.6 as build-python

RUN \
  apt-get -y update && \
  apt-get install --no-install-recommends -y gettext=0.19.8.1-2 && \
  # Cleanup apt cache
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

ADD requirements.txt /app/
RUN pip install -r /app/requirements.txt


### Build static assets
FROM node:8.6.0 as build-nodejs

ARG STATIC_URL

# Install node_modules
ADD webpack.config.js app.json package.json package-lock.json /app/
WORKDIR /app
RUN npm install

# Build static
ADD ./saleor/static /app/saleor/static/
ADD ./templates /app/templates/
RUN \
  STATIC_URL=${STATIC_URL} \
  npm run build-assets --production && \
  npm run build-emails --production


### Final image
FROM python:3.6-slim

ARG AWS_ACCESS_KEY_ID
ARG AWS_LOCATION
ARG AWS_MEDIA_BUCKET_NAME
ARG AWS_SECRET_ACCESS_KEY
ARG AWS_STORAGE_BUCKET_NAME
ARG STATIC_URL

RUN \
  apt-get update && \
  apt-get install -y --no-install-recommends \
    libxml2="2.9.4+dfsg1-2.2+deb9u2" \
    libssl1.1="1.1.0f-3+deb9u2" \
    libcairo2="1.14.8-1" \
    libpango-1.0-0="1.40.5-1" \
    libpangocairo-1.0-0="1.40.5-1" \
    libgdk-pixbuf2.0-0="2.36.5-2+deb9u2" \
    shared-mime-info="1.8-1+deb9u1" \
    mime-support="3.60" && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

ADD . /app
COPY --from=build-python /usr/local/lib/python3.6/site-packages/ /usr/local/lib/python3.6/site-packages/
COPY --from=build-python /usr/local/bin/ /usr/local/bin/
COPY --from=build-nodejs /app/saleor/static /app/saleor/static
COPY --from=build-nodejs /app/webpack-bundle.json /app/
COPY --from=build-nodejs /app/templates /app/templates
WORKDIR /app

RUN useradd --system saleor && \
    mkdir /app/media /app/static && \
    chown -R saleor:saleor /app/

USER saleor

RUN SECRET_KEY=dummy \
    AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \
    AWS_LOCATION=${AWS_LOCATION} \
    AWS_MEDIA_BUCKET_NAME=${AWS_MEDIA_BUCKET_NAME} \
    AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \
    AWS_STORAGE_BUCKET_NAME=${AWS_STORAGE_BUCKET_NAME} \
    STATIC_URL=${STATIC_URL} \
    python3 manage.py collectstatic --no-input
EXPOSE 8000
ENV PORT 8000

ENV PYTHONUNBUFFERED 1
ENV PROCESSES 4
CMD ["uwsgi", "/app/saleor/wsgi/uwsgi.ini"]
