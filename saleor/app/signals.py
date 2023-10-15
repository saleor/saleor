from ..core.tasks import delete_from_storage_task


def delete_brand_images(sender, instance, **kwargs):
    if img := instance.brand_logo_default:
        delete_from_storage_task.delay(img.name)
