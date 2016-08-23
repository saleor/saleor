FROM python:3.5
ENV PYTHONUNBUFFERED 1

RUN \
 apt-get -y update && \
 apt-get install -y apt-transport-https

RUN \
 apt-key adv --keyserver keyserver.ubuntu.com --recv 68576280 && \
 echo 'deb https://deb.nodesource.com/node_6.x jessie main' | tee /etc/apt/sources.list.d/nodesource.list && \
 echo 'deb-src https://deb.nodesource.com/node_6.x jessie main' | tee -a /etc/apt/sources.list.d/nodesource.list

RUN \
 apt-get -y update && \
 apt-get install -y nodejs && \
 apt-get clean

ADD requirements.txt /app/requirements.txt
RUN cd /app && pip install -r requirements.txt

ADD package.json /app/package.json
RUN cd /app && npm install

RUN useradd -ms /bin/bash saleor

ADD . /app
WORKDIR /app

ENV PATH $PATH:/app/node_modules/.bin
RUN npm run build-assets
RUN SECRET_KEY=tmpkey python manage.py collectstatic --noinput

EXPOSE 8000
ENV PORT 8000

ENTRYPOINT ["/app/compose/entrypoint.sh"]
CMD ["uwsgi saleor/wsgi/uwsgi.ini"]
