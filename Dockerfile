FROM python:3.5
ENV PYTHONUNBUFFERED 1

ENV SECRET_KEY=123

RUN \
  apt-get -y update && \
  apt-get install -y gettext npm && \
  apt-get clean

ADD . /app
RUN pip install -r /app/requirements.txt
RUN python /app/manage.py migrate
RUN npm i n -g && n v6.11.1
RUN npm i webpack yarn -g
RUN yarn
RUN yarn run build-assets
RUN django-admin.py compilemessages

WORKDIR /app

EXPOSE 8000
ENV PORT 8000


CMD ["uwsgi", "/app/saleor/wsgi/uwsgi.ini"]
