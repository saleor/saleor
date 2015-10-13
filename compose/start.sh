#!/bin/bash

bower install
grunt
saleor collectstatic --noinput

gunicorn saleor.wsgi.static -b 0.0.0.0:8000 --log-file -
