from ..core.tasks import delete_from_storage_task


def delete_avatar(sender, instance, **kwargs):
    if avatar := instance.avatar:
        delete_from_storage_task.delay(avatar.name)
