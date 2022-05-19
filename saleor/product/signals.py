from ..core.tasks import delete_from_storage_task, delete_product_media_task
from ..core.utils import delete_versatile_image


def delete_background_image(sender, instance, **kwargs):
    if img := instance.background_image:
        delete_versatile_image(img)


def delete_digital_content_file(sender, instance, **kwargs):
    if file := instance.content_file:
        delete_from_storage_task.delay(file.path)


def delete_product_all_media(sender, instance, **kwargs):
    if all_media := instance.media.all():
        for media in all_media:
            media.set_to_remove()
            delete_product_media_task.delay(media.id)
