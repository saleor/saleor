from unittest.mock import patch

import graphene
import pytest
from prices import Money, TaxedMoney

from .....discount.utils.promotion import get_active_catalogue_promotion_rules
from .....order import OrderEvents, OrderStatus
from .....order.models import OrderEvent, OrderLine
from .....product.models import ProductVariant
from .....tests.utils import flush_post_commit_hooks
from ....tests.utils import get_graphql_content

DELETE_VARIANT_BY_SKU_MUTATION = """
    mutation variantDelete($sku: String) {
        productVariantDelete(sku: $sku) {
            productVariant {
                sku
                id
            }
            }
        }
"""


@patch("saleor.plugins.manager.PluginsManager.product_variant_deleted")
@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_variant_by_sku(
    mocked_recalculate_orders_task,
    product_variant_deleted_webhook_mock,
    staff_api_client,
    product,
    permission_manage_products,
):
    # given
    variant = product.variants.first()
    variant_sku = variant.sku
    variables = {"sku": variant_sku}

    # when
    response = staff_api_client.post_graphql(
        DELETE_VARIANT_BY_SKU_MUTATION,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantDelete"]

    # then
    product_variant_deleted_webhook_mock.assert_called_once_with(variant)
    assert data["productVariant"]["sku"] == variant_sku
    with pytest.raises(variant._meta.model.DoesNotExist):
        variant.refresh_from_db()
    mocked_recalculate_orders_task.assert_not_called()
    for rule in get_active_catalogue_promotion_rules():
        assert rule.variants_dirty


DELETE_VARIANT_MUTATION = """
    mutation variantDelete($id: ID!) {
        productVariantDelete(id: $id) {
            productVariant {
                sku
                id
            }
            }
        }
"""


@patch("saleor.plugins.manager.PluginsManager.product_variant_deleted")
@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_variant(
    mocked_recalculate_orders_task,
    product_variant_deleted_webhook_mock,
    staff_api_client,
    product,
    permission_manage_products,
):
    query = DELETE_VARIANT_MUTATION
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variant_sku = variant.sku
    variables = {"id": variant_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantDelete"]

    product_variant_deleted_webhook_mock.assert_called_once_with(variant)
    assert data["productVariant"]["sku"] == variant_sku
    with pytest.raises(variant._meta.model.DoesNotExist):
        variant.refresh_from_db()
    mocked_recalculate_orders_task.assert_not_called()
    for rule in get_active_catalogue_promotion_rules():
        assert rule.variants_dirty


def test_delete_variant_remove_checkout_lines(
    staff_api_client,
    checkout_with_items,
    permission_manage_products,
):
    query = DELETE_VARIANT_MUTATION
    line = checkout_with_items.lines.first()
    variant = line.variant
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantDelete"]

    assert data["productVariant"]["sku"] == variant.sku
    with pytest.raises(variant._meta.model.DoesNotExist):
        variant.refresh_from_db()
    with pytest.raises(line._meta.model.DoesNotExist):
        line.refresh_from_db()


@patch("saleor.product.signals.delete_from_storage_task.delay")
@patch("saleor.plugins.manager.PluginsManager.product_variant_deleted")
@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_variant_with_image(
    mocked_recalculate_orders_task,
    product_variant_deleted_webhook_mock,
    delete_from_storage_task_mock,
    staff_api_client,
    variant_with_image,
    permission_manage_products,
    media_root,
):
    """Ensure deleting variant doesn't delete linked product image."""

    query = DELETE_VARIANT_MUTATION
    variant = variant_with_image

    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantDelete"]

    product_variant_deleted_webhook_mock.assert_called_once_with(variant)
    assert data["productVariant"]["sku"] == variant.sku
    with pytest.raises(variant._meta.model.DoesNotExist):
        variant.refresh_from_db()
    mocked_recalculate_orders_task.assert_not_called()
    delete_from_storage_task_mock.assert_not_called()


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_variant_in_draft_order(
    mocked_recalculate_orders_task,
    staff_api_client,
    order_line,
    permission_manage_products,
    order_list,
    channel_USD,
):
    query = DELETE_VARIANT_MUTATION

    draft_order = order_line.order
    draft_order.status = OrderStatus.DRAFT
    draft_order.save(update_fields=["status"])

    variant = order_line.variant
    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variables = {"id": variant_id}

    product = variant.product
    net = variant.get_price(variant_channel_listing)
    gross = Money(amount=net.amount, currency=net.currency)
    order_not_draft = order_list[-1]
    unit_price = TaxedMoney(net=net, gross=gross)
    quantity = 3
    order_line_not_in_draft = OrderLine.objects.create(
        variant=variant,
        order=order_not_draft,
        product_name=str(product),
        variant_name=str(variant),
        product_sku=variant.sku,
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        unit_price=unit_price,
        total_price=unit_price * quantity,
        quantity=quantity,
    )
    order_line_not_in_draft_pk = order_line_not_in_draft.pk
    second_draft_order = order_list[0]
    second_draft_order.status = OrderStatus.DRAFT
    second_draft_order.save(update_fields=["status"])
    OrderLine.objects.create(
        variant=variant,
        order=second_draft_order,
        product_name=str(product),
        variant_name=str(variant),
        product_sku=variant.sku,
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        unit_price=unit_price,
        total_price=unit_price * quantity,
        quantity=quantity,
    )
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    content = get_graphql_content(response)
    data = content["data"]["productVariantDelete"]
    assert data["productVariant"]["sku"] == variant.sku
    with pytest.raises(order_line._meta.model.DoesNotExist):
        order_line.refresh_from_db()

    assert OrderLine.objects.filter(pk=order_line_not_in_draft_pk).exists()
    expected_call_args = sorted([second_draft_order.id, draft_order.id])
    result_call_args = sorted(mocked_recalculate_orders_task.mock_calls[0].args[0])

    assert result_call_args == expected_call_args

    events = OrderEvent.objects.filter(type=OrderEvents.ORDER_LINE_VARIANT_DELETED)
    assert events
    assert {event.order for event in events} == {draft_order, second_draft_order}
    assert {event.user for event in events} == {staff_api_client.user}
    expected_params = [
        {
            "item": str(line),
            "line_pk": line.pk,
            "quantity": line.quantity,
        }
        for line in draft_order.lines.all()
    ]
    for param in expected_params:
        assert param in events.get(order=draft_order).parameters
    expected_params = [
        {
            "item": str(line),
            "line_pk": line.pk,
            "quantity": line.quantity,
        }
        for line in second_draft_order.lines.all()
    ]
    for param in expected_params:
        assert param in events.get(order=second_draft_order).parameters


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_default_variant(
    mocked_recalculate_orders_task,
    staff_api_client,
    product_with_two_variants,
    permission_manage_products,
):
    # given
    query = DELETE_VARIANT_MUTATION
    product = product_with_two_variants

    default_variant = product.variants.first()
    second_variant = product.variants.last()

    product.default_variant = default_variant
    product.save(update_fields=["default_variant"])

    assert second_variant.pk != default_variant.pk

    variant_id = graphene.Node.to_global_id("ProductVariant", default_variant.pk)
    variables = {"id": variant_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariantDelete"]
    assert data["productVariant"]["sku"] == default_variant.sku
    with pytest.raises(default_variant._meta.model.DoesNotExist):
        default_variant.refresh_from_db()

    product.refresh_from_db()
    assert product.default_variant.pk == second_variant.pk
    mocked_recalculate_orders_task.assert_not_called()


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_not_default_variant_left_default_variant_unchanged(
    mocked_recalculate_orders_task,
    staff_api_client,
    product_with_two_variants,
    permission_manage_products,
):
    # given
    query = DELETE_VARIANT_MUTATION
    product = product_with_two_variants

    default_variant = product.variants.first()
    second_variant = product.variants.last()

    product.default_variant = default_variant
    product.save(update_fields=["default_variant"])

    assert second_variant.pk != default_variant.pk

    variant_id = graphene.Node.to_global_id("ProductVariant", second_variant.pk)
    variables = {"id": variant_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariantDelete"]
    assert data["productVariant"]["sku"] == second_variant.sku
    with pytest.raises(second_variant._meta.model.DoesNotExist):
        second_variant.refresh_from_db()

    product.refresh_from_db()
    assert product.default_variant.pk == default_variant.pk
    mocked_recalculate_orders_task.assert_not_called()


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_default_all_product_variant_left_product_default_variant_unset(
    mocked_recalculate_orders_task,
    staff_api_client,
    product,
    permission_manage_products,
):
    # given
    query = DELETE_VARIANT_MUTATION

    default_variant = product.variants.first()

    product.default_variant = default_variant
    product.save(update_fields=["default_variant"])

    assert product.variants.count() == 1

    variant_id = graphene.Node.to_global_id("ProductVariant", default_variant.pk)
    variables = {"id": variant_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productVariantDelete"]
    assert data["productVariant"]["sku"] == default_variant.sku
    with pytest.raises(default_variant._meta.model.DoesNotExist):
        default_variant.refresh_from_db()

    product.refresh_from_db()
    assert not product.default_variant
    mocked_recalculate_orders_task.assert_not_called()


@patch("saleor.plugins.manager.PluginsManager.product_variant_deleted")
@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_variant_delete_product_channel_listing_without_available_channel(
    mocked_recalculate_orders_task,
    product_variant_deleted_webhook_mock,
    staff_api_client,
    product,
    permission_manage_products,
):
    """Test that the product is unlisted if all listed variants are removed."""
    # given
    query = DELETE_VARIANT_MUTATION
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variant_sku = variant.sku
    variables = {"id": variant_id}

    # second variant not available
    ProductVariant.objects.create(product=product, sku="not-available-variant")

    assert product.channel_listings.count() == 1

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantDelete"]

    product_variant_deleted_webhook_mock.assert_called_once_with(variant)
    assert data["productVariant"]["sku"] == variant_sku
    with pytest.raises(variant._meta.model.DoesNotExist):
        variant.refresh_from_db()
    mocked_recalculate_orders_task.assert_not_called()
    product.refresh_from_db()
    assert product.channel_listings.count() == 0


@patch("saleor.plugins.manager.PluginsManager.product_variant_deleted")
@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_variant_delete_product_channel_listing_not_deleted(
    mocked_recalculate_orders_task,
    product_variant_deleted_webhook_mock,
    staff_api_client,
    product_with_two_variants,
    permission_manage_products,
):
    """Test that the product listing persists if any variant listings remain."""
    # given
    query = DELETE_VARIANT_MUTATION
    product = product_with_two_variants
    variant = product.variants.first()
    variant_id = graphene.Node.to_global_id("ProductVariant", variant.pk)
    variant_sku = variant.sku
    variables = {"id": variant_id}

    product_channel_listing_count = product.channel_listings.count()

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantDelete"]

    product_variant_deleted_webhook_mock.assert_called_once_with(variant)
    assert data["productVariant"]["sku"] == variant_sku
    with pytest.raises(variant._meta.model.DoesNotExist):
        variant.refresh_from_db()
    mocked_recalculate_orders_task.assert_not_called()
    product.refresh_from_db()
    assert product.channel_listings.count() == product_channel_listing_count


DELETE_VARIANT_BY_EXTERNAL_REFERENCE = """
    mutation variantDelete($id: ID, $externalReference: String) {
        productVariantDelete(id: $id, externalReference: $externalReference) {
            productVariant {
                externalReference
                id
            }
            errors {
                field
                message
            }
        }
    }
"""


@patch("saleor.plugins.manager.PluginsManager.product_variant_deleted")
@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_variant_by_external_reference(
    mocked_recalculate_orders_task,
    product_variant_deleted_webhook_mock,
    staff_api_client,
    product,
    permission_manage_products,
):
    # given
    query = DELETE_VARIANT_BY_EXTERNAL_REFERENCE
    ext_ref = "test-ext-ref"
    variant = product.variants.first()
    variant.external_reference = ext_ref
    variant.save(update_fields=["external_reference"])
    variables = {"externalReference": ext_ref}

    # when
    response = staff_api_client.post_graphql(
        query,
        variables,
        permissions=[permission_manage_products],
    )
    content = get_graphql_content(response)
    flush_post_commit_hooks()
    data = content["data"]["productVariantDelete"]

    # then
    product_variant_deleted_webhook_mock.assert_called_once_with(variant)
    assert data["productVariant"]["externalReference"] == ext_ref
    assert data["productVariant"]["id"] == graphene.Node.to_global_id(
        variant._meta.model.__name__, variant.id
    )
    with pytest.raises(variant._meta.model.DoesNotExist):
        variant.refresh_from_db()
    mocked_recalculate_orders_task.assert_not_called()


def test_delete_product_by_both_id_and_external_reference(
    staff_api_client, permission_manage_products
):
    # given
    query = DELETE_VARIANT_BY_EXTERNAL_REFERENCE
    variables = {"externalReference": "whatever", "id": "whatever"}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productVariantDelete"]["errors"]
    assert (
        errors[0]["message"]
        == "Argument 'id' cannot be combined with 'external_reference'"
    )


def test_delete_product_by_external_reference_not_existing(
    staff_api_client, permission_manage_products
):
    # given
    query = DELETE_VARIANT_BY_EXTERNAL_REFERENCE
    ext_ref = "non-existing-ext-ref"
    variables = {"externalReference": ext_ref}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productVariantDelete"]["errors"]
    assert errors[0]["message"] == f"Couldn't resolve to a node: {ext_ref}"
