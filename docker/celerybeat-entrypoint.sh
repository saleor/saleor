#!/bin/bash

# Wait for rabbitmq to be available
./wait-for-it.sh 127.0.0.1:5672 --timeout=600 -- echo "RabbitMQ is up!"

celery -A saleor beat --loglevel DEBUG -S django
