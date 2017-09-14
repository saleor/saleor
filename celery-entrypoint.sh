#!/bin/bash

# Wait for rabbitmq to be available
./wait-for-it.sh rabbitmq:5672 --timeout=600 -- echo "RabbitMQ is up!"
# Wait for webapp to be available
./wait-for-it.sh web:8000 --timeout=600 -- echo "OYE Records Server is up!"

celery -A saleor worker --loglevel INFO
