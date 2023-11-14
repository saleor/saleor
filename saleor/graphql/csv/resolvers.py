from ...csv import models
from ..core.context import get_database_connection_name


def resolve_export_file(info, id):
    return (
        models.ExportFile.objects.using(get_database_connection_name(info.context))
        .filter(id=id)
        .first()
    )


def resolve_export_files(info):
    return models.ExportFile.objects.using(
        get_database_connection_name(info.context)
    ).all()
