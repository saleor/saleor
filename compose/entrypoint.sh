#!/bin/bash
set -e

USER=saleor
APP_UID=$(stat -c "%u" /app)

export DATABASE_URL=postgres://$DB_ENV_DB_USER:$DB_ENV_DB_PASS@db/$DB_ENV_DB_NAME
export REDIS_URL=redis://redis:6379/0

if [ "$APP_UID" != "0" ]; then
    if [ "$APP_UID" != "$(id -u $USER)" ]; then
        usermod -u "$APP_UID" $USER
    fi
    su $USER -c "PATH=$PATH:/app/node_modules/.bin $@"
fi

exec "$@"
