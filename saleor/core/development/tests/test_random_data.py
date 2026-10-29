from decimal import Decimal
from unittest.mock import Mock

import pytest
from django.core.files.storage import default_storage
from django.db.models import Count
from django.test import override_settings
from django.utils.crypto import get_random_string

from ....account.models import Address, User
from ....account.tests.fixtures.user import dangerously_get_or_create_superuser
from ....attribute.models import AttributeValue
from ....channel.models import Channel
from ....discount.models import (
    Promotion,
    PromotionRule,
    Voucher,
    VoucherChannelListing,
    VoucherCode,
)
from ....giftcard.models import GiftCard, GiftCardEvent
from ....order import OrderOrigin
from ....order.models import Order
from ....product import ProductTypeKind
from ....product.models import Product, ProductMedia, ProductType, VariantMedia
from ....shipping.models import ShippingZone
from ....tax.models import TaxClass, TaxClassCountryRate
from .. import random_data


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
    assert not Address.objects.exists()

    assert User.objects.all().count() == 0
    random_data.create_fake_user(get_random_string(length=50))
    assert User.objects.all().count() == 1
    user = User.objects.all().first()
    assert not user.is_superuser

    assert Address.objects.all().count() == 1
    assert user.addresses.count() == 1


def test_create_fake_users(db):
    how_many = 5
    for _ in random_data.create_users(get_random_string(length=50), how_many):
        pass
    assert User.objects.all().count() == 5


def test_create_fake_order(db, monkeypatch, image, media_root, warehouse):
    # Tests shouldn't depend on images present in placeholder folder
    monkeypatch.setattr(
        "saleor.core.development.random_data.get_image", Mock(return_value=image)
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
