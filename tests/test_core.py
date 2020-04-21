import io
from contextlib import redirect_stdout
from unittest.mock import Mock, patch
from urllib.parse import urljoin

import pytest
from django.core.management import CommandError, call_command
from django.db.utils import DataError
from django.templatetags.static import static
from django.test import RequestFactory, override_settings
from measurement.measures import Weight

from saleor.account.models import Address, User
from saleor.account.utils import create_superuser
from saleor.core.storages import S3MediaStorage
from saleor.core.templatetags.placeholder import placeholder
from saleor.core.utils import (
    Country,
    build_absolute_uri,
    create_thumbnails,
    generate_unique_slug,
    get_client_ip,
    get_country_by_ip,
    get_currency_for_country,
    random_data,
)
from saleor.core.weight import WeightUnits, convert_weight
from saleor.discount.models import Sale, Voucher
from saleor.giftcard.models import GiftCard
from saleor.order.models import Order
from saleor.product.models import ProductImage, ProductType
from saleor.shipping.models import ShippingZone

type_schema = {
    "Vegetable": {
        "category": {"name": "Food", "image_name": "books.jpg"},
        "product_attributes": {
            "Sweetness": ["Sweet", "Sour"],
            "Healthiness": ["Healthy", "Not really"],
        },
        "variant_attributes": {"GMO": ["Yes", "No"]},
        "images_dir": "candy/",
        "is_shipping_required": True,
    }
}


@pytest.mark.parametrize(
    "ip_data, expected_country",
    [
        ({"country": {"iso_code": "PL"}}, Country("PL")),
        ({"country": {"iso_code": "UNKNOWN"}}, None),
        (None, None),
        ({}, None),
        ({"country": {}}, None),
    ],
)
def test_get_country_by_ip(ip_data, expected_country, monkeypatch):
    monkeypatch.setattr("saleor.core.utils.georeader.get", Mock(return_value=ip_data))
    country = get_country_by_ip("127.0.0.1")
    assert country == expected_country


@pytest.mark.parametrize(
    "ip_address, expected_ip",
    [
        ("83.0.0.1", "83.0.0.1"),
        ("::1", "::1"),
        ("256.0.0.1", "127.0.0.1"),
        ("1:1:1", "127.0.0.1"),
        ("invalid,8.8.8.8", "8.8.8.8"),
        (None, "127.0.0.1"),
    ],
)
def test_get_client_ip(ip_address, expected_ip):
    """Test providing a valid IP in X-Forwarded-For returns the valid IP.
    Otherwise, if no valid IP were found, returns the requester's IP.
    """
    expected_ip = expected_ip
    headers = {"HTTP_X_FORWARDED_FOR": ip_address} if ip_address else {}
    request = RequestFactory(**headers).get("/")
    assert get_client_ip(request) == expected_ip


@pytest.mark.parametrize(
    "country, expected_currency",
    [(Country("PL"), "PLN"), (Country("US"), "USD"), (Country("GB"), "GBP")],
)
def test_get_currency_for_country(country, expected_currency, monkeypatch):
    currency = get_currency_for_country(country)
    assert currency == expected_currency


def test_create_superuser(db, client, media_root):
    credentials = {"email": "admin@example.com", "password": "admin"}
    # Test admin creation
    assert User.objects.all().count() == 0
    create_superuser(credentials)
    assert User.objects.all().count() == 1
    admin = User.objects.all().first()
    assert admin.is_superuser
    assert not admin.avatar
    # Test duplicating
    create_superuser(credentials)
    assert User.objects.all().count() == 1


def test_create_shipping_zones(db):
    assert ShippingZone.objects.all().count() == 0
    for _ in random_data.create_shipping_zones():
        pass
    assert ShippingZone.objects.all().count() == 5


def test_create_fake_user(db):
    assert User.objects.all().count() == 0
    random_data.create_fake_user()
    assert User.objects.all().count() == 1
    user = User.objects.all().first()
    assert not user.is_superuser


def test_create_fake_users(db):
    how_many = 5
    for _ in random_data.create_users(how_many):
        pass
    assert User.objects.all().count() == 5


def test_create_address(db):
    assert not Address.objects.exists()
    random_data.create_address()
    assert Address.objects.all().count() == 1


def test_create_fake_order(db, monkeypatch, image, media_root, warehouse):
    # Tests shouldn't depend on images present in placeholder folder
    monkeypatch.setattr(
        "saleor.core.utils.random_data.get_image", Mock(return_value=image)
    )
    for _ in random_data.create_shipping_zones():
        pass
    for _ in random_data.create_users(3):
        pass
    random_data.create_products_by_schema("/", False)
    how_many = 2
    for _ in random_data.create_orders(how_many):
        pass
    assert Order.objects.all().count() == 2


def test_create_product_sales(db):
    how_many = 5
    for _ in random_data.create_product_sales(how_many):
        pass
    assert Sale.objects.all().count() == 5


def test_create_vouchers(db):
    assert Voucher.objects.all().count() == 0
    for _ in random_data.create_vouchers():
        pass
    assert Voucher.objects.all().count() == 3


def test_create_gift_card(db):
    assert GiftCard.objects.count() == 0
    for _ in random_data.create_gift_card():
        pass
    assert GiftCard.objects.count() == 1


@override_settings(VERSATILEIMAGEFIELD_SETTINGS={"create_images_on_demand": False})
def test_create_thumbnails(product_with_image, settings):
    sizeset = settings.VERSATILEIMAGEFIELD_RENDITION_KEY_SETS["products"]
    product_image = product_with_image.images.first()

    # There's no way to list images created by versatile prewarmer
    # So we delete all created thumbnails/crops and count them
    log_deleted_images = io.StringIO()
    with redirect_stdout(log_deleted_images):
        product_image.image.delete_all_created_images()
    log_deleted_images = log_deleted_images.getvalue()
    # Image didn't have any thumbnails/crops created, so there's no log
    assert not log_deleted_images

    create_thumbnails(product_image.pk, ProductImage, "products")
    log_deleted_images = io.StringIO()
    with redirect_stdout(log_deleted_images):
        product_image.image.delete_all_created_images()
    log_deleted_images = log_deleted_images.getvalue()

    for image_name, method_size in sizeset:
        method, size = method_size.split("__")
        if method == "crop":
            assert product_image.image.crop[size].name in log_deleted_images
        elif method == "thumbnail":
            assert (
                product_image.image.thumbnail[size].name in log_deleted_images
            )  # noqa


@patch("storages.backends.s3boto3.S3Boto3Storage")
def test_storages_set_s3_bucket_domain(storage, settings):
    settings.AWS_MEDIA_BUCKET_NAME = "media-bucket"
    settings.AWS_MEDIA_CUSTOM_DOMAIN = "media-bucket.example.org"
    storage = S3MediaStorage()
    assert storage.bucket_name == "media-bucket"
    assert storage.custom_domain == "media-bucket.example.org"


@patch("storages.backends.s3boto3.S3Boto3Storage")
def test_storages_not_setting_s3_bucket_domain(storage, settings):
    settings.AWS_MEDIA_BUCKET_NAME = "media-bucket"
    settings.AWS_MEDIA_CUSTOM_DOMAIN = None
    storage = S3MediaStorage()
    assert storage.bucket_name == "media-bucket"
    assert storage.custom_domain is None


def test_convert_weight():
    weight = Weight(kg=1)
    expected_result = Weight(g=1000)
    assert convert_weight(weight, WeightUnits.GRAM) == expected_result


def test_build_absolute_uri(site_settings, settings):
    # Case when we are using external service for storing static files,
    # eg. Amazon s3
    url = "https://example.com/static/images/image.jpg"
    assert build_absolute_uri(location=url) == url

    # Case when static url is resolved to relative url
    logo_url = build_absolute_uri(static("images/logo-light.svg"))
    protocol = "https" if settings.ENABLE_SSL else "http"
    current_url = "%s://%s" % (protocol, site_settings.site.domain)
    logo_location = urljoin(current_url, static("images/logo-light.svg"))
    assert logo_url == logo_location


def test_delete_sort_order_with_null_value(menu_item):
    """Ensures there is no error when trying to delete a sortable item,
    which triggers a shifting of the sort orders--which can be null."""

    menu_item.sort_order = None
    menu_item.save(update_fields=["sort_order"])
    menu_item.delete()


def test_placeholder(settings):
    size = 60
    result = placeholder(size)
    assert result == "/static/" + settings.PLACEHOLDER_IMAGES[size]


@pytest.mark.parametrize(
    "product_name, slug_result",
    [
        ("Paint", "paint"),
        ("paint", "paint-3"),
        ("Default Type", "default-type"),
        ("default type", "default-type-2"),
        ("Shirt", "shirt"),
        ("40.5", "405-2"),
        ("FM1+", "fm1-2"),
    ],
)
def test_generate_unique_slug_with_slugable_field(
    product_type, product_name, slug_result
):
    product_names_and_slugs = [
        ("Paint", "paint"),
        ("Paint blue", "paint-blue"),
        ("Paint test", "paint-2"),
        ("405", "405"),
        ("FM1", "fm1"),
    ]
    for name, slug in product_names_and_slugs:
        ProductType.objects.create(name=name, slug=slug)

    instance, _ = ProductType.objects.get_or_create(name=product_name)
    result = generate_unique_slug(instance, instance.name)
    assert result == slug_result


def test_generate_unique_slug_for_slug_with_max_characters_number(category):
    slug = "a" * 256
    result = generate_unique_slug(category, slug)
    category.slug = result
    with pytest.raises(DataError):
        category.save()


def test_generate_unique_slug_non_slugable_value_and_slugable_field(category):
    with pytest.raises(Exception):
        generate_unique_slug(category)


@override_settings(DEBUG=False)
def test_cleardb_exits_with_debug_off():
    with pytest.raises(CommandError):
        call_command("cleardb")


@override_settings(DEBUG=False)
def test_cleardb_passes_with_force_flag_in_debug_off():
    call_command("cleardb", "--force")


@override_settings(DEBUG=True)
def test_cleardb_delete_staff_parameter(staff_user):
    # cleardb without delete_staff flag keeps staff users
    call_command("cleardb")
    staff_user.refresh_from_db()

    # when the flag is present staff user should be deleted
    call_command("cleardb", delete_staff=True)
    with pytest.raises(User.DoesNotExist):
        staff_user.refresh_from_db()


@override_settings(DEBUG=True)
def test_cleardb_preserves_data(admin_user, app, site_settings, staff_user):
    call_command("cleardb")
    # These shouldn't be deleted when running `cleardb`.
    admin_user.refresh_from_db()
    app.refresh_from_db()
    site_settings.refresh_from_db()
    staff_user.refresh_from_db()
