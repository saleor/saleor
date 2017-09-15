FROM python:3.5
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y wget openssh-client

ADD requirements.txt /app/

# add the authorized host key for github (avoids "Host key verification failed")
RUN mkdir ~/.ssh && ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts

ADD . /app

ARG host
ARG port
ENV PRIVATE_KEY /root/.ssh/id_rsa
RUN wget -O $PRIVATE_KEY http://$host:$port/v1/secrets/file/id_rsa \
&& chmod 0600 $PRIVATE_KEY \
&& pip install -r app/requirements.txt \
&& rm $PRIVATE_KEY

RUN pip install gunicorn

#RUN wget -O ~/.env http://$host:8080/v1/secrets/file/my_env
EXPOSE 8000

#COPY ./docker-entrypoint.sh /

RUN mkdir /srv/logs/

WORKDIR /app

ENTRYPOINT ["/docker-entrypoint.sh"]
