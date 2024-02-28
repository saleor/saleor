from django.conf import settings


def get_database_connection_name(allow_replica: bool):
    if allow_replica:
        return settings.DATABASE_CONNECTION_REPLICA_NAME
    return settings.DATABASE_CONNECTION_DEFAULT_NAME
