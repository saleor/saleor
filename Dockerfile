FROM python:3.4
ENV PYTHONUNBUFFERED 1

RUN \
 apt-get -y update && \
 apt-get install -y npm && \
 apt-get clean && \
 ln -s /usr/bin/nodejs /usr/bin/node

ADD setup.py /app/setup.py
RUN cd /app && pip install -e .[PaaS]

ADD package.json /node/package.json
RUN cd /node && npm install

ADD . /app
WORKDIR /app

EXPOSE 8000
ENTRYPOINT ["/app/compose/entrypoint.sh"]
