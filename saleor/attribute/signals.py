from ..core.tasks import delete_from_storage


def delete_attribute_value_file(sender, instance, **kwargs):
    if file_url := instance.file_url:
        delete_from_storage.delay(file_url)
