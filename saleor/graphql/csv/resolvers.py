from django.conf import settings

from ...csv import models


def resolve_export_file(id):
    return (
        models.ExportFile.objects.using(settings.DATABASE_CONNECTION_REPLICA_NAME)
        .filter(id=id)
        .first()
    )


def resolve_export_files():
    return models.ExportFile.objects.using(
        settings.DATABASE_CONNECTION_REPLICA_NAME
    ).all()
