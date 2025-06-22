#!/bin/bash
# Script to load update-automation-snapshot into our database (to public schema)
# It needs the docker compose from saleor platform repository: https://github.com/saleor/saleor-platform
# Tested only on MacOs

DIR="$( cd "$( dirname "$0" )" && pwd )"
SNAPSHOT=$DIR"/update-automation-snapshot.sql"
# make sure to use `public` schema
sed -i '' 's/update_automation_snapshot_staging_saleor_cloud/public/' $SNAPSHOT
sed -i '' 's/update_automation_snapshot_staging_saleor_cloud/public/' $SNAPSHOT

# please note that you should not use this password on production services
DB_URL="postgresql://saleor:saleor@localhost:5432/"
# use different database for testing purpose
FULL_DB_URL=$DB_URL"e2e"

# drop previous database
psql $DB_URL -c 'DROP DATABASE IF EXISTS e2e WITH(FORCE);'

# create new database and make sure to install needed extensions
psql $DB_URL -c 'CREATE DATABASE e2e;'
psql $FULL_DB_URL -c 'CREATE EXTENSION IF NOT EXISTS btree_gin; CREATE EXTENSION IF NOT EXISTS pg_trgm;'

# load the snapshot
psql $FULL_DB_URL -f $SNAPSHOT

# make sure to run migrations in case snapshot is not up to date with `core` migrations
docker compose exec api python manage.py migrate
