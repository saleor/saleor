from decimal import Decimal
from unittest.mock import Mock, patch
from urllib.parse import urljoin

import pytest
from django.core.files.storage import default_storage
from django.core.management import CommandError, call_command
from django.db.models import Count
from django.db.utils import DataError
from django.templatetags.static import static
from django.test import RequestFactory, override_settings
from django.utils.crypto import get_random_string

from ...account.models import Address, User
from ...account.tests.fixtures.user import dangerously_get_or_create_superuser
from ...attribute.models import AttributeValue
from ...channel.models import Channel
from ...discount.models import (
    Promotion,
    PromotionRule,
    Voucher,
    VoucherChannelListing,
    VoucherCode,
)
from ...giftcard.models import GiftCard, GiftCardEvent
from ...order import OrderOrigin
from ...order.models import Order
from ...payment.models import TransactionItem
from ...product import ProductTypeKind
from ...product.models import Product, ProductMedia, ProductType, VariantMedia
from ...shipping.models import ShippingZone
from ...tax.models import TaxClass, TaxClassCountryRate
from ..storages import S3MediaStorage
from ..utils import (
    build_absolute_uri,
    generate_unique_slug,
    get_client_ip,
    get_domain,
    is_ssl_enabled,
    prepare_unique_attribute_value_slug,
    random_data,
)

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
    ("ip_address", "expected_ip"),
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
    expected_ip = expected_ip
    headers = {"HTTP_X_FORWARDED_FOR": ip_address} if ip_address else {}
    request = RequestFactory(**headers).get("/")
    assert get_client_ip(request) == expected_ip


def test_create_superuser(db, client, media_root):
    credentials = {
        "email": "admin@example.com",
        "password": get_random_string(length=50),
    }
    # Test admin creation
    assert User.objects.all().count() == 0
    dangerously_get_or_create_superuser(**credentials)
    assert User.objects.all().count() == 1
    admin = User.objects.all().first()
    assert admin.is_superuser
    assert not admin.avatar
    # Test duplicating
    dangerously_get_or_create_superuser(**credentials)
    assert User.objects.all().count() == 1


def test_create_shipping_zones(db):
    assert ShippingZone.objects.all().count() == 0
    for _ in random_data.create_shipping_zones():
        pass
    assert ShippingZone.objects.all().count() == 5


def test_create_channels(db):
    assert Channel.objects.all().count() == 0
    for _ in random_data.create_channels():
        pass
    assert Channel.objects.all().count() == 2
    assert Channel.objects.get(slug="channel-pln")


@override_settings(DEFAULT_CHANNEL_SLUG="test-slug")
def test_create_channels_with_default_channel_slug(db):
    assert Channel.objects.all().count() == 0
    for _ in random_data.create_channels():
        pass
    assert Channel.objects.all().count() == 2
    assert Channel.objects.get(slug="test-slug")


def test_create_fake_user(db):
    assert User.objects.all().count() == 0
    random_data.create_fake_user(get_random_string(length=50))
    assert User.objects.all().count() == 1
    user = User.objects.all().first()
    assert not user.is_superuser


def test_create_fake_users(db):
    how_many = 5
    for _ in random_data.create_users(get_random_string(length=50), how_many):
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
    for _ in random_data.create_channels():
        pass
    for _ in random_data.create_shipping_zones():
        pass
    for _ in random_data.create_users(get_random_string(length=50), 3):
        pass
    for _ in random_data.create_page_type():
        pass
    for _ in random_data.create_pages():
        pass
    random_data.create_products_by_schema("/", False)
    how_many_orders = 2
    for _ in random_data.create_orders(how_many_orders):
        pass
    assert Order.objects.all().count() == how_many_orders
    assert (
        list(Order.objects.values_list("origin", flat=True))
        == [OrderOrigin.CHECKOUT] * how_many_orders
    )


def test_create_products_deletes_retired_products(product_type, category):
    retired_product_pks = (127, 132, 133)
    Product.objects.bulk_create(
        [
            Product(
                pk=product_pk,
                name=f"Retired product {product_pk}",
                slug=f"retired-product-{product_pk}",
                product_type=product_type,
                category=category,
            )
            for product_pk in retired_product_pks
        ]
    )
    current_product = Product.objects.create(
        name="Current product",
        slug="current-product",
        product_type=product_type,
        category=category,
    )
    assert set(
        Product.objects.filter(pk__in=retired_product_pks).values_list("pk", flat=True)
    ) == set(retired_product_pks)

    random_data.create_products([], "/", False)

    assert Product.objects.filter(pk__in=retired_product_pks).exists() is False
    assert Product.objects.get(pk=current_product.pk) == current_product


def test_create_missing_product_images_does_not_duplicate_images(product, monkeypatch):
    placeholder_dir = "/placeholder"
    existing_image_name = "existing.png"
    missing_image_name = "missing.png"
    image_names = (existing_image_name, missing_image_name)
    ProductMedia.objects.create(
        product=product, image=f"products/{existing_image_name}"
    )

    def create_product_image(product, _placeholder_dir, image_name):
        return ProductMedia.objects.create(
            product=product, image=f"products/{image_name}"
        )

    create_product_image_mock = Mock(side_effect=create_product_image)
    monkeypatch.setattr(random_data, "create_product_image", create_product_image_mock)

    random_data.create_missing_product_images(product, placeholder_dir, image_names)
    random_data.create_missing_product_images(product, placeholder_dir, image_names)

    assert set(product.media.values_list("image", flat=True)) == {
        f"products/{existing_image_name}",
        f"products/{missing_image_name}",
    }
    create_product_image_mock.assert_called_once_with(
        product, placeholder_dir, missing_image_name
    )


def test_get_matching_placeholder_image_name_with_storage_suffix():
    image_name = "sample.png"
    stored_image_name = "products/sample_8f3a1.png"

    result = random_data.get_matching_placeholder_image_name(
        stored_image_name, (image_name, "other.png")
    )

    assert result == image_name


def test_assign_media_to_product_variants_removes_stale_relations(variant, monkeypatch):
    expected_image_name = "expected.png"
    expected_media = ProductMedia.objects.create(
        product=variant.product, image=f"products/{expected_image_name}"
    )
    stale_media = ProductMedia.objects.create(
        product=variant.product, image="products/stale.png"
    )
    VariantMedia.objects.bulk_create(
        [
            VariantMedia(variant=variant, media=expected_media),
            VariantMedia(variant=variant, media=stale_media),
        ]
    )
    monkeypatch.setattr(
        random_data,
        "IMAGES_MAPPING",
        {variant.product_id: [expected_image_name]},
    )
    monkeypatch.setattr(
        random_data,
        "VARIANT_IMAGES_MAPPING",
        {variant.pk: (expected_image_name,)},
    )

    random_data.assign_media_to_product_variants()

    assert list(
        VariantMedia.objects.filter(variant=variant).values_list("media_id", flat=True)
    ) == [expected_media.pk]


def test_create_tax_classes_is_idempotent(db):
    juice_product_type = ProductType.objects.create(
        name="Juice",
        slug="juice",
        kind=ProductTypeKind.NORMAL,
    )
    expected_tax_classes = {
        1: "Groceries",
        2: "Books",
        3: "No taxes",
    }
    expected_default_rate_count = 9
    expected_tax_class_rate_count = 25
    assert juice_product_type.tax_class_id is None

    for _ in random_data.create_tax_classes():
        pass
    for _ in random_data.create_tax_classes():
        pass

    assert (
        dict(
            TaxClass.objects.filter(pk__in=expected_tax_classes).values_list(
                "pk", "name"
            )
        )
        == expected_tax_classes
    )
    assert (
        TaxClassCountryRate.objects.filter(tax_class=None).count()
        == expected_default_rate_count
    )
    assert (
        TaxClassCountryRate.objects.filter(
            tax_class_id__in=expected_tax_classes
        ).count()
        == expected_tax_class_rate_count
    )
    books_france_rate = TaxClassCountryRate.objects.get(
        tax_class_id=random_data.BOOKS_TAX_CLASS_PK,
        country="FR",
    )
    assert books_france_rate.rate == Decimal("5.5")
    juice_product_type.refresh_from_db(fields=("tax_class",))
    assert juice_product_type.tax_class_id == random_data.GROCERIES_TAX_CLASS_PK


def test_create_attribute_file_values_is_idempotent(
    file_attribute, icon_image, media_root, monkeypatch, tmp_path
):
    file_name = "sample.png"
    content_type = "image/png"
    source_dir = tmp_path / random_data.ATTRIBUTE_FILES_DIR
    source_dir.mkdir()
    (source_dir / file_name).write_bytes(icon_image.read())
    attribute_value = AttributeValue.objects.create(
        attribute=file_attribute,
        name=file_name,
        slug="sample-file",
    )
    monkeypatch.setattr(
        random_data,
        "ATTRIBUTE_FILE_MAPPING",
        {attribute_value.pk: (file_name, content_type)},
    )
    expected_storage_path = f"file_upload/{file_name}"

    random_data.create_attribute_file_values(str(tmp_path))
    random_data.create_attribute_file_values(str(tmp_path))

    attribute_value.refresh_from_db(fields=("file_url", "content_type"))
    assert attribute_value.file_url == expected_storage_path
    assert attribute_value.content_type == content_type
    assert default_storage.exists(expected_storage_path) is True
    assert default_storage.listdir("file_upload") == ([], [file_name])


def test_create_attribute_file_values_rejects_invalid_mime_type(
    file_attribute, media_root, monkeypatch, tmp_path
):
    file_name = "invalid.png"
    content_type = "image/png"
    source_dir = tmp_path / random_data.ATTRIBUTE_FILES_DIR
    source_dir.mkdir()
    (source_dir / file_name).write_bytes(b"invalid image content")
    attribute_value = AttributeValue.objects.create(
        attribute=file_attribute,
        name=file_name,
        slug="invalid-file",
    )
    monkeypatch.setattr(
        random_data,
        "ATTRIBUTE_FILE_MAPPING",
        {attribute_value.pk: (file_name, content_type)},
    )
    expected_storage_path = f"file_upload/{file_name}"

    with pytest.raises(
        ValueError,
        match="does not match its allowed content type image/png",
    ):
        random_data.create_attribute_file_values(str(tmp_path))

    attribute_value.refresh_from_db(fields=("file_url", "content_type"))
    assert attribute_value.file_url is None
    assert attribute_value.content_type is None
    assert default_storage.exists(expected_storage_path) is False


def test_create_catalogue_promotions(db):
    how_many = 5
    for _ in random_data.create_channels():
        pass
    channel_count = Channel.objects.count()
    expected_rule_count = how_many * 2

    for _ in random_data.create_catalogue_promotions(how_many):
        pass

    assert Promotion.objects.all().count() == how_many
    assert PromotionRule.objects.all().count() == expected_rule_count
    assert (
        list(
            PromotionRule.objects.annotate(channel_count=Count("channels"))
            .order_by("pk")
            .values_list("channel_count", flat=True)
        )
        == [channel_count] * expected_rule_count
    )

    for _ in random_data.create_catalogue_promotions(how_many):
        pass

    assert Promotion.objects.all().count() == how_many
    assert PromotionRule.objects.all().count() == expected_rule_count
    assert (
        list(
            PromotionRule.objects.annotate(channel_count=Count("channels"))
            .order_by("pk")
            .values_list("channel_count", flat=True)
        )
        == [channel_count] * expected_rule_count
    )


def test_create_order_promotions(db):
    how_many = 5
    for _ in random_data.create_channels():
        pass
    channel_count = Channel.objects.count()
    expected_rule_count = how_many * 2

    for _ in random_data.create_order_promotions(how_many):
        pass

    assert Promotion.objects.all().count() == how_many
    assert PromotionRule.objects.all().count() == expected_rule_count
    assert (
        list(
            PromotionRule.objects.annotate(channel_count=Count("channels"))
            .order_by("pk")
            .values_list("channel_count", flat=True)
        )
        == [channel_count] * expected_rule_count
    )

    for _ in random_data.create_order_promotions(how_many):
        pass

    assert Promotion.objects.all().count() == how_many
    assert PromotionRule.objects.all().count() == expected_rule_count
    assert (
        list(
            PromotionRule.objects.annotate(channel_count=Count("channels"))
            .order_by("pk")
            .values_list("channel_count", flat=True)
        )
        == [channel_count] * expected_rule_count
    )


def test_create_vouchers(db):
    voucher_count = 4
    single_use_voucher_name = "Single Use Vouchers"
    single_use_code_count = 50
    single_use_codes = {
        f"SINGLE-USE-{index:03}" for index in range(1, single_use_code_count + 1)
    }
    expected_code_count = single_use_code_count + voucher_count - 1
    channel_count = 0
    for _ in random_data.create_channels():
        channel_count += 1
    assert Voucher.objects.all().count() == 0
    for _ in random_data.create_vouchers():
        pass
    assert Voucher.objects.all().count() == voucher_count
    assert VoucherCode.objects.all().count() == expected_code_count
    assert VoucherChannelListing.objects.all().count() == voucher_count * channel_count
    single_use_voucher = Voucher.objects.get(name=single_use_voucher_name)
    assert (
        set(single_use_voucher.codes.values_list("code", flat=True)) == single_use_codes
    )

    for _ in random_data.create_vouchers():
        pass

    assert Voucher.objects.all().count() == voucher_count
    assert VoucherCode.objects.all().count() == expected_code_count
    assert VoucherChannelListing.objects.all().count() == voucher_count * channel_count
    single_use_voucher = Voucher.objects.get(name=single_use_voucher_name)
    assert (
        set(single_use_voucher.codes.values_list("code", flat=True)) == single_use_codes
    )


def test_create_gift_card(
    db, product, shippable_gift_card_product, customer_user, staff_user, order
):
    product = shippable_gift_card_product
    product.name = "Gift card 100"
    product.save(update_fields=["name"])

    amount = 5
    assert GiftCard.objects.count() == 0
    assert GiftCardEvent.objects.count() == 0
    for _ in random_data.create_gift_cards(amount):
        pass
    assert GiftCard.objects.count() == amount * 2
    assert GiftCardEvent.objects.count() == amount * 2


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


def test_build_absolute_uri():
    # Case when we are using external service for storing static files,
    # eg. Amazon s3
    url = "https://example.com/static/images/image.jpg"
    assert build_absolute_uri(location=url) == url

    # Case when static url is resolved to relative url
    logo_url = build_absolute_uri(static("images/close.svg"))
    current_url = "https://example.com/"
    logo_location = urljoin(current_url, static("images/close.svg"))
    assert logo_url == logo_location


def test_build_absolute_uri_with_host(settings):
    settings.PUBLIC_URL = None
    settings.ENABLE_SSL = True
    # given
    host = "test.com"
    location = "images/close.svg"

    # when
    url = build_absolute_uri(location, host)

    # then
    assert url == f"https://{host}/{location}"


@pytest.mark.parametrize(
    "public_url", ["https://api.example.com", "http://api.example.com"]
)
@pytest.mark.parametrize("enable_ssl", [True, False])
@pytest.mark.parametrize("host", [None, "test.com"])
def test_build_absolute_uri_with_public_url(public_url, enable_ssl, host, settings):
    # given
    location = "images/close.svg"
    settings.PUBLIC_URL = public_url
    settings.ENABLE_SSL = enable_ssl
    # when
    url = build_absolute_uri(location, host)
    # then
    assert url == f"{public_url}/{location}"


def test_build_absolute_uri_with_public_url_and_absolute_location(settings):
    # given
    location = "https://example.com/static/images/image.jpg"
    settings.PUBLIC_URL = "https://api.example.com"
    # when
    url = build_absolute_uri(location)
    # then
    assert url == location


@pytest.mark.parametrize("enable_ssl", [True, False])
def test_is_ssl_enabled(enable_ssl, settings):
    settings.PUBLIC_URL = None
    # given
    settings.ENABLE_SSL = enable_ssl
    # then
    assert is_ssl_enabled() == enable_ssl


@pytest.mark.parametrize(
    ("public_url", "expected"),
    [("https://api.example.com", True), ("http://api.example.com", False)],
)
@pytest.mark.parametrize("enable_ssl", [True, False])
def test_is_ssl_enabled_with_public_url(public_url, expected, enable_ssl, settings):
    # given
    settings.PUBLIC_URL = public_url
    settings.ENABLE_SSL = enable_ssl
    # then
    assert is_ssl_enabled() == expected


def test_get_domain(site_settings, settings):
    settings.PUBLIC_URL = None
    assert get_domain() == site_settings.site.domain


def test_get_domain_with_public_url(site_settings, settings):
    # given
    domain = "api.example.com"
    settings.PUBLIC_URL = f"https://{domain}"
    assert get_domain() == domain


def test_delete_sort_order_with_null_value(menu_item):
    menu_item.sort_order = None
    menu_item.save(update_fields=["sort_order"])
    menu_item.delete()


@pytest.mark.parametrize(
    ("product_name", "slug_result"),
    [
        ("Paint", "paint"),
        ("paint", "paint-3"),
        ("Default Type", "default-type"),
        ("default type", "default-type-2"),
        ("Shirt", "shirt"),
        ("40.5", "405-2"),
        ("FM1+", "fm1-2"),
        ("Ładny", "ladny"),
        ("زيوت", "zywt"),
        ("わたし-わ にっぽん です", "watasi-wa-nitupon-desu-2"),
        ("Салеор", "saleor-2"),
    ],
)
def test_generate_unique_slug_with_slugable_field(
    product_type, product_name, slug_result
):
    product_names_and_slugs = [
        ("Paint", "paint"),
        ("Paint blue", "paint-blue"),
        ("Paint test", "paint-2"),
        ("Saleor", "saleor"),
        ("405", "405"),
        ("FM1", "fm1"),
        ("わたし わ にっぽん です", "watasi-wa-nitupon-desu"),
    ]
    for name, slug in product_names_and_slugs:
        ProductType.objects.create(
            name=name,
            slug=slug,
            kind=ProductTypeKind.NORMAL,
        )

    instance, _ = ProductType.objects.get_or_create(name=product_name)
    result = generate_unique_slug(instance, instance.name)
    assert result == slug_result


def test_generate_unique_slug_for_slug_with_max_characters_number(category):
    slug = "a" * 256
    result = generate_unique_slug(category, slug)
    category.slug = result
    with pytest.raises(DataError):
        category.save()


def test_generate_unique_slug_with_additional_lookup_slug_not_changed(
    color_attribute, attribute_without_values
):
    # given
    value_1 = color_attribute.values.first()

    # when
    value_2 = AttributeValue(name=value_1.name, attribute=attribute_without_values)

    # then
    result = generate_unique_slug(
        value_2,
        value_2.name,
        additional_search_lookup={"attribute": value_2.attribute_id},
    )

    assert result == value_1.slug


def test_generate_unique_slug_with_additional_lookup_slug_changed(color_attribute):
    # given
    value_1 = color_attribute.values.first()

    # when
    value_2 = AttributeValue(name=value_1.name, attribute=color_attribute)

    # then
    result = generate_unique_slug(
        value_2,
        value_2.name,
        additional_search_lookup={"attribute": value_2.attribute_id},
    )

    assert result == f"{value_1.slug}-2"


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


@override_settings(DEBUG=True)
def test_cleardb_remove_orders_and_transactions(transaction_item):
    transaction_item.refresh_from_db()

    call_command("cleardb")
    with pytest.raises(TransactionItem.DoesNotExist):
        transaction_item.refresh_from_db()
    with pytest.raises(Order.DoesNotExist):
        transaction_item.order.refresh_from_db()


def test_prepare_unique_attribute_value_slug(color_attribute):
    # given
    value_1 = color_attribute.values.first()

    # when
    value_2 = AttributeValue(
        name=value_1.name, attribute=color_attribute, slug=value_1.slug
    )

    # then
    result = prepare_unique_attribute_value_slug(value_2.attribute, value_2.slug)

    assert result == f"{value_1.slug}-2"


def test_prepare_unique_attribute_value_slug_non_existing_slug(color_attribute):
    # when
    non_existing_slug = "non-existing-slug"

    # then
    result = prepare_unique_attribute_value_slug(color_attribute, non_existing_slug)

    assert result == non_existing_slug
