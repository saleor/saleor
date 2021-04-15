from ..core.tasks import delete_from_storage_task
from ..core.utils import delete_versatile_image


def delete_background_image(sender, instance, **kwargs):
    if img := instance.background_image:
        delete_versatile_image(img)


def delete_product_media_image(sender, instance, **kwargs):
    if img := instance.image:
        delete_versatile_image(img)


def delete_digital_content_file(sender, instance, **kwargs):
    if file := instance.content_file:
        delete_from_storage_task.delay(file.path)
