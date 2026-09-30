from ..core.tasks import delete_from_storage_task


def delete_media_image(sender, instance, **kwargs):
    """Remove a deleted media's file from storage.

    Wired through `post_delete` rather than called from `BaseMedia.delete()` on
    purpose: media rows are most often removed by a cascade from their owner,
    which never routes through the model's `delete()`.
    """
    if file := instance.image:
        delete_from_storage_task.delay(file.name)
