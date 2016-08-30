FROM python:3.5
ENV PYTHONUNBUFFERED 1

ADD . /app
RUN pip install -r /app/requirements.txt
WORKDIR /app

EXPOSE 8000
ENV PORT 8000

CMD ["uwsgi", "/app/saleor/wsgi/uwsgi.ini"]
