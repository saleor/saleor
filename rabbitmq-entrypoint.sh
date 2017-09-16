#!/usr/bin/env bash
set -e

(
count=0;
# Execute list_users until service is up and running
until timeout 5 rabbitmqctl list_users >/dev/null 2>/dev/null || (( count++ >= 60 )); do sleep 1; done;
if rabbitmqctl list_users | grep guest > /dev/null
then
   # Delete default user and create new users
   rabbitmqctl delete_user guest

   rabbitmqctl add_user admin ${RABBITMQ_ADMIN_PASSWORD}
   rabbitmqctl set_user_tags admin administrator
   rabbitmqctl set_permissions -p / admin  ".*" ".*" ".*"

   rabbitmqctl add_user ${RABBITMQ_USER} ${RABBITMQ_PASSWORD}
   rabbitmqctl set_permissions -p / ${RABBITMQ_USER}  ".*" ".*" ".*"
   echo "setup completed"
else
   echo "already setup"
fi
) &

# Call original entrypoint
exec docker-entrypoint.sh rabbitmq-server $@
