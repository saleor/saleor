from django.core.files.storage import default_storage

from ..tasks import delete_from_storage_task


def test_delete_from_storage_task(product_with_image, media_root):
    # given
    path = product_with_image.media.first().image.path
    assert default_storage.exists(path)

    # when
    delete_from_storage_task(path)

    # then
    assert not default_storage.exists(path)


def test_delete_from_storage_task_file_that_not_exists(media_root):
    """Ensure method not fail when trying to remove not existing file."""
    # given
    path = "random/test-path"
    assert not default_storage.exists(path)

    # when
    delete_from_storage_task(path)
