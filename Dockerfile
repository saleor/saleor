FROM python:3.5
ENV PYTHONUNBUFFERED 1

# https://unix.stackexchange.com/a/508948
RUN echo "deb [check-valid-until=no] http://cdn-fastly.deb.debian.org/debian jessie main" > /etc/apt/sources.list.d/jessie.list
RUN echo "deb [check-valid-until=no] http://archive.debian.org/debian jessie-backports main" > /etc/apt/sources.list.d/jessie-backports.list
RUN sed -i '/deb http:\/\/deb.debian.org\/debian jessie-updates main/d' /etc/apt/sources.list
# RUN apt-get -o Acquire::Check-Valid-Until=false update


RUN apt-get -o Acquire::Check-Valid-Until=false update && apt-get -o Acquire::Check-Valid-Until=false install -y wget openssh-client

ADD requirements.txt /app/

# add the authorized host key for github (avoids "Host key verification failed")
RUN mkdir ~/.ssh && ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts


ARG host

ENV PRIVATE_KEY /root/.ssh/id_rsa

RUN wget -O $PRIVATE_KEY http://$host:8080/v1/secrets/file/id_rsa \
&& chmod 0600 $PRIVATE_KEY \
&& pip install -r app/requirements.txt \
&& rm $PRIVATE_KEY

RUN pip install gunicorn

ADD . /app

EXPOSE 8000

RUN mkdir /srv/logs/

WORKDIR /app

ENTRYPOINT ["/docker-entrypoint.sh"]
