FROM python:3.5-buster
ENV PYTHONUNBUFFERED 1

RUN apt-get -y update --allow-insecure-repositories && apt-get --allow-unauthenticated install -y wget openssh-client

ADD requirements.txt /app/
WORKDIR /app

# add the authorized host key for github (avoids "Host key verification failed")
RUN mkdir ~/.ssh && ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts


ARG host

ENV PRIVATE_KEY /root/.ssh/id_rsa

RUN wget -O $PRIVATE_KEY http://$host:8080/v1/secrets/file/id_rsa \
  && chmod 0600 $PRIVATE_KEY \
  && pip install -r requirements.txt \
  && rm $PRIVATE_KEY

RUN pip install gunicorn

ADD . /app

EXPOSE 8000

RUN mkdir /srv/logs/


ENTRYPOINT ["/docker-entrypoint.sh"]
