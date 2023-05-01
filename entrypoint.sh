#!/bin/sh

set -e

echo "Adding ECS Private IPs to ALLOWED_HOSTS..."
ECS_PRIVATE_IPS=$(wget -qO- "${ECS_CONTAINER_METADATA_URI}" | jq -r '.Networks | map(.IPv4Addresses) | flatten | join(",")')
export ALLOWED_HOSTS="${ALLOWED_HOSTS}${ECS_PRIVATE_IPS:+,$ECS_PRIVATE_IPS}"

echo "Running migrations..."
python manage.py migrate --no-input

exec "$@"
