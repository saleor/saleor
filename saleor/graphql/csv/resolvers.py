from ...csv import models


def resolve_export_file(id):
    return models.ExportFile.objects.filter(id=id).first()


def resolve_export_files():
    return models.ExportFile.objects.all()
