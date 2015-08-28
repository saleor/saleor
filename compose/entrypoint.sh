#!/bin/bash
set -e

USER=saleor

export DATABASE_URL=postgres://$DB_ENV_DB_USER:$DB_ENV_DB_PASS@db/$DB_ENV_DB_NAME

if [ $(cat /etc/passwd | grep $USER | wc -l) == "0" ]; then
  useradd -u `stat -c "%u" /app` -m $USER
fi

chown $USER.$USER /node -R
if [[ ( $1 == "/app/compose/start.sh" ) && ( ! -d "/app/node_modules" ) ]]; then
  echo Copying /node/node_modules to /app/node_modules..
  su saleor -c "cp -r /node/node_modules /app"
fi

su saleor -c "PATH=$PATH:/app/node_modules/.bin $*"
