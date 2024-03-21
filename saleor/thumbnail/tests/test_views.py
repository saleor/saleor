from unittest.mock import patch

import graphene
from PIL import Image

from .. import IconThumbnailFormat, ThumbnailFormat
from ..models import Thumbnail


def test_handle_thumbnail_view_with_format(client, category_with_image, settings):
    # given
    size = 60
    format = ThumbnailFormat.WEBP
    category_id = graphene.Node.to_global_id("Category", category_with_image.id)
    thumbnail_count = Thumbnail.objects.count()

    # when
    response = client.get(f"/thumbnail/{category_id}/{size}/{format}/")

    # then
    assert response.status_code == 302
    file_path, _ = category_with_image.background_image.name.rsplit(".")
    assert (
        response.url
        == settings.MEDIA_URL + f"thumbnails/{file_path}_thumbnail_64.{format.lower()}"
    )
    assert Thumbnail.objects.count() == thumbnail_count + 1


def test_handle_thumbnail_view_for_category(client, category_with_image, settings):
    # given
    size = 60
    category_id = graphene.Node.to_global_id("Category", category_with_image.id)
    thumbnail_count = 0

    # when
    response = client.get(f"/thumbnail/{category_id}/{size}/")

    # then
    assert response.status_code == 302
    file_path, ext = category_with_image.background_image.name.rsplit(".")
    assert (
        response.url
        == settings.MEDIA_URL + f"thumbnails/{file_path}_thumbnail_64.{ext}"
    )
    assert Thumbnail.objects.count() == thumbnail_count + 1


def test_handle_thumbnail_view_for_collection(client, collection_with_image, settings):
    # given
    size = 100
    collection_id = graphene.Node.to_global_id("Collection", collection_with_image.id)
    thumbnail_count = Thumbnail.objects.count()

    # when
    response = client.get(f"/thumbnail/{collection_id}/{size}/")

    # then
    assert response.status_code == 302
    file_path, ext = collection_with_image.background_image.name.rsplit(".")
    assert (
        response.url
        == settings.MEDIA_URL + f"thumbnails/{file_path}_thumbnail_128.{ext}"
    )
    assert Thumbnail.objects.count() == thumbnail_count + 1


def test_handle_thumbnail_view_for_user(
    client, staff_user, image, media_root, settings
):
    # given
    staff_user.avatar = image
    staff_user.save(update_fields=["avatar"])

    size = 200
    user_uuid = graphene.Node.to_global_id("User", staff_user.uuid)
    thumbnail_count = Thumbnail.objects.count()

    # when
    response = client.get(f"/thumbnail/{user_uuid}/{size}/")

    # then
    assert response.status_code == 302
    file_path, ext = staff_user.avatar.name.rsplit(".")
    assert (
        response.url
        == settings.MEDIA_URL + f"thumbnails/{file_path}_thumbnail_256.{ext}"
    )
    assert Thumbnail.objects.count() == thumbnail_count + 1


def test_handle_thumbnail_view_for_product_media(
    client, staff_user, product_with_image, settings
):
    # given
    product_media = product_with_image.media.first()

    size = 500
    product_media_id = graphene.Node.to_global_id("ProductMedia", product_media.id)
    thumbnail_count = Thumbnail.objects.count()

    # when
    response = client.get(f"/thumbnail/{product_media_id}/{size}/")

    # then
    assert response.status_code == 302
    file_path, ext = product_media.image.name.rsplit(".")
    assert (
        response.url
        == settings.MEDIA_URL + f"thumbnails/{file_path}_thumbnail_512.{ext}"
    )
    assert Thumbnail.objects.count() == thumbnail_count + 1


def test_handle_thumbnail_view_for_category_thumbnail_already_exist(
    client, category, settings, image, media_root
):
    # given
    size = 64
    thumbnail = Thumbnail.objects.create(category=category, size=size, image=image)
    category_id = graphene.Node.to_global_id("Category", category.id)
    thumbnail_count = Thumbnail.objects.count()

    # when
    response = client.get(f"/thumbnail/{category_id}/{size}/")

    # then
    assert response.status_code == 302
    assert response.url == thumbnail.image.url
    assert Thumbnail.objects.count() == thumbnail_count


def test_handle_thumbnail_view_for_collection_thumbnail_already_exist(
    client, collection, settings, image, media_root
):
    # given
    size = 128
    thumbnail = Thumbnail.objects.create(collection=collection, size=128, image=image)
    collection_id = graphene.Node.to_global_id("Collection", collection.id)
    thumbnail_count = Thumbnail.objects.count()

    # when
    response = client.get(f"/thumbnail/{collection_id}/{size}/")

    # then
    assert response.status_code == 302
    assert response.url == thumbnail.image.url
    assert Thumbnail.objects.count() == thumbnail_count


def test_handle_thumbnail_view_for_user_thumbnail_already_exist(
    client, staff_user, settings, image, media_root
):
    # given
    size = 128
    thumbnail = Thumbnail.objects.create(user=staff_user, size=128, image=image)
    user_uuid = graphene.Node.to_global_id("User", staff_user.uuid)
    thumbnail_count = Thumbnail.objects.count()

    # when
    response = client.get(f"/thumbnail/{user_uuid}/{size}/")

    # then
    assert response.status_code == 302
    assert response.url == thumbnail.image.url
    assert Thumbnail.objects.count() == thumbnail_count


def test_handle_thumbnail_view_for_product_media_thumbnail_already_exist(
    client, product_with_image, settings, image, media_root
):
    # given
    product_media = product_with_image.media.first()
    size = 256
    thumbnail = Thumbnail.objects.create(
        product_media=product_media, size=256, image=image
    )
    product_media_id = graphene.Node.to_global_id("ProductMedia", product_media.id)
    thumbnail_count = Thumbnail.objects.count()

    # when
    response = client.get(f"/thumbnail/{product_media_id}/{size}/")

    # then
    assert response.status_code == 302
    assert response.url == thumbnail.image.url
    assert Thumbnail.objects.count() == thumbnail_count


def test_handle_thumbnail_view_no_image(client, category):
    # given
    size = 60
    category_id = graphene.Node.to_global_id("Category", category.id)

    # when
    response = client.get(f"/thumbnail/{category_id}/{size}/")

    # then
    assert response.status_code == 404


def test_handle_thumbnail_view_invalid_object_type(client, order):
    # given
    size = 60
    order_id = graphene.Node.to_global_id("Order", order.id)

    # when
    response = client.get(f"/thumbnail/{order_id}/{size}/")

    # then
    assert response.status_code == 404


def test_handle_thumbnail_view_invalid_format(client, category):
    # given
    size = 60
    category_id = graphene.Node.to_global_id("Category", category.id)

    # when
    response = client.get(f"/thumbnail/{category_id}/{size}/XYZ/")

    # then
    assert response.status_code == 404


def test_handle_icon_thumbnail_view_invalid_format(client, app):
    # given
    app_uuid = graphene.Node.to_global_id("App", app.uuid)

    # when
    response = client.get(f"/thumbnail/{app_uuid}/60/XYZ/")

    # then
    assert response.status_code == 404


def test_handle_thumbnail_view_invalid_instance_id(client, category):
    # given
    size = 60
    category_id = category.id

    # when
    response = client.get(f"/thumbnail/{category_id}/{size}/")

    # then
    assert response.status_code == 404


def test_handle_thumbnail_view_object_does_not_exists(client):
    # given
    size = 60
    category_id = graphene.Node.to_global_id("Category", 1)

    # when
    response = client.get(f"/thumbnail/{category_id}/{size}/")

    # then
    assert response.status_code == 404


@patch("saleor.thumbnail.utils.magic.from_buffer")
def test_handle_thumbnail_view_invalid_image_mime_type(
    from_buffer_mock, client, category_with_image
):
    # given
    size = 60
    category_id = graphene.Node.to_global_id("Category", category_with_image.id)
    thumbnail_count = Thumbnail.objects.count()

    invalid_mime_type = "application/x-empty"
    from_buffer_mock.return_value = invalid_mime_type

    # when
    response = client.get(f"/thumbnail/{category_id}/{size}/")

    # then
    assert response.status_code == 400
    assert response.content.decode("utf-8") == "Invalid image."
    assert Thumbnail.objects.count() == thumbnail_count


def test_handle_thumbnail_view_image_does_not_exist(
    client, staff_user, product_with_image, settings
):
    # given
    product_media = product_with_image.media.first()
    product_media.image.name = "invalid_image.jpg"
    product_media.save(update_fields=["image"])

    size = 500
    product_media_id = graphene.Node.to_global_id("ProductMedia", product_media.id)
    thumbnail_count = Thumbnail.objects.count()

    # when
    response = client.get(f"/thumbnail/{product_media_id}/{size}/")

    # then
    assert response.status_code == 404
    assert response.content.decode("utf-8") == "Cannot found image file."
    assert Thumbnail.objects.count() == thumbnail_count


def test_handle_icon_thumbnail_view_with_format(
    client, app, icon_image, media_root, settings
):
    # given
    app.brand_logo_default = icon_image
    app.save(update_fields=["brand_logo_default"])

    size = 60
    format = IconThumbnailFormat.WEBP
    app_uuid = graphene.Node.to_global_id("App", app.uuid)
    thumbnail_count = Thumbnail.objects.count()

    # when
    response = client.get(f"/thumbnail/{app_uuid}/{size}/{format}/")

    # then
    assert response.status_code == 302
    file_path, _ = app.brand_logo_default.name.rsplit(".")
    assert (
        response.url
        == settings.MEDIA_URL + f"thumbnails/{file_path}_thumbnail_64.{format.lower()}"
    )
    assert Thumbnail.objects.count() == thumbnail_count + 1

    thumbnail = Thumbnail.objects.last()
    with Image.open(thumbnail.image) as image:
        assert image.format == "WEBP"


def test_handle_thumbnail_view_for_app_logo_default(
    client, app, icon_image, media_root, settings
):
    # given
    app.brand_logo_default = icon_image
    app.save(update_fields=["brand_logo_default"])

    size = 200
    uuid = graphene.Node.to_global_id("App", app.uuid)
    thumbnail_count = Thumbnail.objects.count()

    # when
    response = client.get(f"/thumbnail/{uuid}/{size}/")

    # then
    assert response.status_code == 302
    file_path, ext = app.brand_logo_default.name.rsplit(".")
    assert (
        response.url
        == settings.MEDIA_URL + f"thumbnails/{file_path}_thumbnail_256.{ext}"
    )
    assert Thumbnail.objects.count() == thumbnail_count + 1


def test_handle_thumbnail_view_for_app_logo_default_thumbnail_exist(
    client, app, icon_image, media_root, settings
):
    # given
    size = 128
    thumbnail = Thumbnail.objects.create(app=app, size=128, image=icon_image)
    uuid = graphene.Node.to_global_id("App", app.uuid)
    thumbnail_count = Thumbnail.objects.count()

    # when
    response = client.get(f"/thumbnail/{uuid}/{size}/")

    # then
    assert response.status_code == 302
    assert response.url == thumbnail.image.url
    assert Thumbnail.objects.count() == thumbnail_count


def test_handle_thumbnail_view_for_app_installation_logo_default(
    client, app_installation, icon_image, media_root, settings
):
    # given
    app_installation.brand_logo_default = icon_image
    app_installation.save(update_fields=["brand_logo_default"])

    size = 200
    uuid = graphene.Node.to_global_id("AppInstallation", app_installation.uuid)
    thumbnail_count = Thumbnail.objects.count()

    # when
    response = client.get(f"/thumbnail/{uuid}/{size}/")

    # then
    assert response.status_code == 302
    file_path, ext = app_installation.brand_logo_default.name.rsplit(".")
    assert (
        response.url
        == settings.MEDIA_URL + f"thumbnails/{file_path}_thumbnail_256.{ext}"
    )
    assert Thumbnail.objects.count() == thumbnail_count + 1


def test_handle_thumbnail_view_for_app_installation_logo_default_thumbnail_exist(
    client, app_installation, icon_image, media_root, settings
):
    # given
    size = 128
    thumbnail = Thumbnail.objects.create(
        app_installation=app_installation, size=128, image=icon_image
    )
    uuid = graphene.Node.to_global_id("AppInstallation", app_installation.uuid)
    thumbnail_count = Thumbnail.objects.count()

    # when
    response = client.get(f"/thumbnail/{uuid}/{size}/")

    # then
    assert response.status_code == 302
    assert response.url == thumbnail.image.url
    assert Thumbnail.objects.count() == thumbnail_count
