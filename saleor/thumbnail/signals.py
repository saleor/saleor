from ..core.tasks import delete_from_storage_task


def delete_thumbnail_image(sender, instance, **kwargs):
    if image := instance.image:
        delete_from_storage_task.delay(image.path)
