FROM python:3.5

ENV PYTHONUNBUFFERED 1

RUN \
  apt-get -y update && \
  apt-get install -y gettext npm && \
  apt-get clean

ADD . /app
WORKDIR /app

RUN pip install -r requirements.txt
RUN npm i n -g && n v6.11.1
RUN npm i webpack yarn -g
RUN yarn
RUN yarn run build-assets


EXPOSE 8000
ENV PORT 8000


CMD ["uwsgi", "/app/saleor/wsgi/uwsgi.ini"]
