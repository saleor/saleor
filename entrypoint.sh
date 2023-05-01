#!/bin/sh

set -e

echo "Running migrations..."
python manage.py migrate --no-input

exec "$@"
