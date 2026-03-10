"""Tests for update_receipt_lines with variant_id and variant creation support."""

import pytest

from ...product.models import ProductVariant
from .. import PurchaseOrderItemStatus, ReceiptStatus
from ..exceptions import ReceiptNotInProgress
from ..models import PurchaseOrderItem, ReceiptLine
from ..receipt_workflow import update_receipt_lines


@pytest.mark.django_db
def test_upsert_by_poi_id(receipt, purchase_order_item, staff_user):
    # given: a receipt and a POI
    # when: updating with purchase_order_item_id
    update_receipt_lines(
        receipt,
        [{"purchase_order_item_id": purchase_order_item.pk, "quantity": 50}],
        user=staff_user,
    )

    # then: a receipt line is created
    line = ReceiptLine.objects.get(
        receipt=receipt, purchase_order_item=purchase_order_item
    )
    assert line.quantity_received == 50
    assert line.received_by == staff_user


@pytest.mark.django_db
def test_upsert_by_variant_creates_poi(
    receipt, purchase_order_item, product_variant_factory, staff_user
):
    # given: a sibling variant (same product, not on shipment)
    sibling = product_variant_factory(sku="SIBLING-1")

    # when: updating with variant (sibling of existing POI's product)
    update_receipt_lines(
        receipt,
        [{"variant": sibling, "quantity": 10}],
        user=staff_user,
    )

    # then: a new POI is auto-created for the sibling variant
    new_poi = PurchaseOrderItem.objects.get(product_variant=sibling)
    assert new_poi.quantity_ordered == 0
    assert new_poi.shipment == receipt.shipment
    assert new_poi.status == PurchaseOrderItemStatus.CONFIRMED

    # and: a receipt line is created for it
    line = ReceiptLine.objects.get(receipt=receipt, purchase_order_item=new_poi)
    assert line.quantity_received == 10


@pytest.mark.django_db
def test_upsert_by_variant_reuses_existing_poi(
    receipt, purchase_order_item, staff_user
):
    # given: a variant that already has a POI on the shipment
    variant = purchase_order_item.product_variant

    # when: updating with variant
    update_receipt_lines(
        receipt,
        [{"variant": variant, "quantity": 30}],
        user=staff_user,
    )

    # then: uses the existing POI (no new POI created)
    assert PurchaseOrderItem.objects.filter(product_variant=variant).count() == 1
    line = ReceiptLine.objects.get(
        receipt=receipt, purchase_order_item=purchase_order_item
    )
    assert line.quantity_received == 30


@pytest.mark.django_db
def test_upsert_updates_existing_line(receipt, purchase_order_item, staff_user):
    # given: an existing receipt line
    ReceiptLine.objects.create(
        receipt=receipt,
        purchase_order_item=purchase_order_item,
        quantity_received=20,
    )

    # when: updating with a new quantity
    update_receipt_lines(
        receipt,
        [{"purchase_order_item_id": purchase_order_item.pk, "quantity": 75}],
        user=staff_user,
    )

    # then: the line is updated, not duplicated
    lines = ReceiptLine.objects.filter(
        receipt=receipt, purchase_order_item=purchase_order_item
    )
    assert lines.count() == 1
    assert lines.first().quantity_received == 75


@pytest.mark.django_db
def test_upsert_zero_deletes_line(receipt, purchase_order_item, staff_user):
    # given: an existing receipt line
    ReceiptLine.objects.create(
        receipt=receipt,
        purchase_order_item=purchase_order_item,
        quantity_received=20,
    )

    # when: updating with quantity 0
    update_receipt_lines(
        receipt,
        [{"purchase_order_item_id": purchase_order_item.pk, "quantity": 0}],
        user=staff_user,
    )

    # then: the line is deleted
    assert not ReceiptLine.objects.filter(
        receipt=receipt, purchase_order_item=purchase_order_item
    ).exists()


@pytest.mark.django_db
def test_rejects_completed_receipt(receipt, purchase_order_item, staff_user):
    # given: a completed receipt
    receipt.status = ReceiptStatus.COMPLETED
    receipt.save(update_fields=["status"])

    # when/then: updating raises ReceiptNotInProgress
    with pytest.raises(ReceiptNotInProgress):
        update_receipt_lines(
            receipt,
            [{"purchase_order_item_id": purchase_order_item.pk, "quantity": 10}],
            user=staff_user,
        )


@pytest.mark.django_db
def test_variant_without_sibling_raises(receipt, staff_user):
    # given: a variant whose product has no POIs on the shipment
    # Create a variant on a different product (no sibling POIs)
    from ...product.models import Product, ProductType, ProductVariant

    product_type = ProductType.objects.create(
        name="Other Type", slug="other-type", has_variants=True
    )
    other_product = Product.objects.create(
        name="Other Product",
        slug="other-product",
        product_type=product_type,
    )
    orphan_variant = ProductVariant.objects.create(
        product=other_product, sku="ORPHAN-1"
    )

    # when/then: raises ValueError
    with pytest.raises(ValueError, match="does not belong to any product"):
        update_receipt_lines(
            receipt,
            [{"variant": orphan_variant, "quantity": 5}],
            user=staff_user,
        )


# --- Tests for product + variant_name (auto-create variant) ---


@pytest.mark.django_db
def test_create_variant_by_name(receipt, purchase_order_item, staff_user):
    # given: a product with existing POIs on the shipment, and a new size name
    product = purchase_order_item.product_variant.product

    # when: updating with product + variant_name
    update_receipt_lines(
        receipt,
        [{"product": product, "variant_name": "XL", "quantity": 7}],
        user=staff_user,
    )

    # then: a new ProductVariant is created
    new_variant = ProductVariant.objects.get(product=product, name="XL")
    assert new_variant.sku == f"{product.slug}-xl"

    # and: a POI is auto-created for it
    new_poi = PurchaseOrderItem.objects.get(product_variant=new_variant)
    assert new_poi.quantity_ordered == 0
    assert new_poi.shipment == receipt.shipment

    # and: a receipt line records the quantity
    line = ReceiptLine.objects.get(receipt=receipt, purchase_order_item=new_poi)
    assert line.quantity_received == 7


@pytest.mark.django_db
def test_create_variant_copies_channel_listings(
    receipt, purchase_order_item, staff_user
):
    # given: a product whose existing variant has channel listings
    product = purchase_order_item.product_variant.product
    sibling = purchase_order_item.product_variant
    sibling_listings = list(sibling.channel_listings.all())
    assert len(sibling_listings) > 0

    # when: creating a new variant
    update_receipt_lines(
        receipt,
        [{"product": product, "variant_name": "XXL", "quantity": 1}],
        user=staff_user,
    )

    # then: channel listings are copied from the sibling
    new_variant = ProductVariant.objects.get(product=product, name="XXL")
    new_listings = list(new_variant.channel_listings.all())
    assert len(new_listings) == len(sibling_listings)
    assert new_listings[0].channel == sibling_listings[0].channel
    assert new_listings[0].price_amount == sibling_listings[0].price_amount


@pytest.mark.django_db
def test_create_variant_assigns_attribute(receipt, purchase_order_item, staff_user):
    # given: product type has a "Size" variant-selection attribute
    product = purchase_order_item.product_variant.product

    # when: creating variant named "3XL"
    update_receipt_lines(
        receipt,
        [{"product": product, "variant_name": "3XL", "quantity": 1}],
        user=staff_user,
    )

    # then: the attribute value is created and assigned
    from ...attribute.models import AttributeValue

    new_variant = ProductVariant.objects.get(product=product, name="3XL")
    attr_value = AttributeValue.objects.get(slug="3xl")
    assert attr_value.name == "3XL"

    assigned = new_variant.attributes.first()
    assert assigned is not None
    assert attr_value in assigned.values.all()


@pytest.mark.django_db
def test_create_variant_reuses_existing_name(
    receipt, purchase_order_item, product_variant_factory, staff_user
):
    # given: a variant named "Medium" already exists on the product
    product = purchase_order_item.product_variant.product
    existing = product_variant_factory(sku="MED-1")
    existing.name = "Medium"
    existing.save(update_fields=["name"])

    # when: updating with variant_name="Medium"
    update_receipt_lines(
        receipt,
        [{"product": product, "variant_name": "Medium", "quantity": 3}],
        user=staff_user,
    )

    # then: no new variant created — reuses the existing one
    assert ProductVariant.objects.filter(product=product, name="Medium").count() == 1
    poi = PurchaseOrderItem.objects.get(product_variant=existing)
    line = ReceiptLine.objects.get(receipt=receipt, purchase_order_item=poi)
    assert line.quantity_received == 3
