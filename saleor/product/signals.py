from ..core.tasks import delete_from_storage


def delete_background_image(sender, instance, **kwargs):
    if img := instance.background_image:
        delete_from_storage.delay(img.name)


def delete_digital_content_file(sender, instance, **kwargs):
    if file := instance.content_file:
        delete_from_storage(file.name)
