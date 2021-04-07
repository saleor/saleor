from django.core.files.storage import default_storage

from ..celeryconf import app


@app.task
def delete_from_storage(path):
    default_storage.delete(path)
