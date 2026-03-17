from ..core.tasks import delete_from_storage_task


def delete_background_image(sender, instance, **kwargs):
    if img := instance.background_image:
        delete_from_storage_task.delay(img.name)


def delete_product_media_image(sender, instance, **kwargs):
    if file := instance.image:
        delete_from_storage_task.delay(file.name)
