#!/bin/bash
set -e

USER=saleor
APP_UID=$(stat -c "%u" /app)

export DATABASE_URL=postgres://$DB_ENV_POSTGRES_USER:$DB_ENV_POSTGRES_PASSWORD@db:5432/$DB_ENV_POSTGRES_USER
export EMAIL_URL=smtp://:@mailcatcher:1025/
export REDIS_URL=redis://redis:6379/0

if [ "$APP_UID" != "0" ]; then
    if [ "$APP_UID" != "$(id -u $USER)" ]; then
        usermod -u "$APP_UID" $USER
    fi
    su $USER -c "PATH=$PATH:/app/node_modules/.bin $*"
fi

$*
