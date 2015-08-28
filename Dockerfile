FROM python:3.4
ENV PYTHONUNBUFFERED 1

RUN \
 apt-get -y update && \
 apt-get install -y npm && \
 apt-get clean && \
 ln -s /usr/bin/nodejs /usr/bin/node

ADD . /app
WORKDIR /app

RUN pip install -r requirements.txt

ADD package.json /node/package.json
RUN cd /node && npm install

EXPOSE 8000
ENTRYPOINT ["/app/compose/entrypoint.sh"]
