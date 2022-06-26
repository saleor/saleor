# syntax=docker/dockerfile:1.2

FROM python:3.5-buster
ENV PYTHONUNBUFFERED 1

RUN apt-get -y update --allow-insecure-repositories && apt-get --allow-unauthenticated install -y wget openssh-client

ADD requirements.txt /app/
WORKDIR /app

# add the authorized host key for github (avoids "Host key verification failed")
RUN mkdir ~/.ssh && ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts

RUN useradd -m user
RUN mkdir -p /home/user/.ssh && ln -s /run/secrets/user_ssh_key /home/user/.ssh/id_rsa
RUN chown -R user:user /home/user/.ssh

RUN --mount=type=ssh,id=github_ssh_key pip install \
    --no-cache \
    --requirement requirements.txt

RUN pip install gunicorn

ADD . /app

EXPOSE 8000

RUN mkdir /srv/logs/


ENTRYPOINT ["/docker-entrypoint.sh"]
