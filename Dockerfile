FROM python:3.5
ENV PYTHONUNBUFFERED 1

RUN \
 apt-get -y update && \
 apt-get install -y npm && \
 apt-get clean && \
 ln -s /usr/bin/nodejs /usr/bin/node

ADD setup.py /app/setup.py
ADD requirements.txt /app/requirements.txt
RUN cd /app && pip install -r requirements.txt

ADD package.json /node/package.json
RUN cd /node && npm install

ADD . /app
WORKDIR /app

EXPOSE 8000
ENTRYPOINT ["/app/compose/entrypoint.sh"]
