import pytest

from ...models import Thumbnail


@pytest.fixture
def thumbnail_product_media(product_media_image, image_list, media_root):
    return Thumbnail.objects.create(
        product_media=product_media_image,
        size=128,
        image=image_list[1],
    )


@pytest.fixture
def thumbnail_category(category_with_image, image_list, media_root):
    return Thumbnail.objects.create(
        category=category_with_image,
        size=128,
        image=image_list[1],
    )


@pytest.fixture
def thumbnail_collection(collection_with_image, image_list, media_root):
    return Thumbnail.objects.create(
        collection=collection_with_image,
        size=128,
        image=image_list[1],
    )


@pytest.fixture
def thumbnail_user(customer_user, image_list, media_root):
    customer_user.avatar = image_list[0]
    return Thumbnail.objects.create(
        user=customer_user,
        size=128,
        image=image_list[1],
    )
