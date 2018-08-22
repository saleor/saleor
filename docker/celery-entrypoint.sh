#!/bin/bash

# Wait for rabbitmq to be available
./wait-for-it.sh 127.0.0.1:5672 --timeout=600 -- echo "RabbitMQ is up!"
# Wait for webapp to be available
./wait-for-it.sh 127.0.0.1:8000 --timeout=600 -- echo "OYE Records Server is up!"

celery -A saleor worker --loglevel INFO -Ofair
