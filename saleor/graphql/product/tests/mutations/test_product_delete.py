from functools import partial
from unittest.mock import ANY, patch

import graphene
import pytest
from django.utils.functional import SimpleLazyObject
from freezegun import freeze_time
from prices import Money, TaxedMoney

from .....attribute.models import AttributeValue
from .....attribute.utils import associate_attribute_values_to_instance
from .....graphql.tests.utils import get_graphql_content
from .....order import OrderEvents, OrderStatus
from .....order.models import OrderEvent, OrderLine
from .....webhook.event_types import WebhookEventAsyncType

DELETE_PRODUCT_MUTATION = """
    mutation DeleteProduct($id: ID!) {
        productDelete(id: $id) {
            product {
                name
                id
                attributes {
                    values {
                        value
                        name
                    }
                }
            }
            errors {
                field
                message
            }
            }
        }
"""


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_product(
    mocked_recalculate_orders_task,
    staff_api_client,
    product,
    permission_manage_products,
):
    query = DELETE_PRODUCT_MUTATION
    node_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productDelete"]
    assert data["product"]["name"] == product.name
    with pytest.raises(product._meta.model.DoesNotExist):
        product.refresh_from_db()
    assert node_id == data["product"]["id"]
    mocked_recalculate_orders_task.assert_not_called()


@patch("saleor.product.signals.delete_from_storage_task.delay")
@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_product_with_image(
    mocked_recalculate_orders_task,
    delete_from_storage_task_mock,
    staff_api_client,
    product_with_image,
    variant_with_image,
    permission_manage_products,
    media_root,
):
    """Ensure deleting product delete also product and variants images from storage."""

    # given
    query = DELETE_PRODUCT_MUTATION
    product = product_with_image
    variant = product.variants.first()
    node_id = graphene.Node.to_global_id("Product", product.id)

    product_img_paths = [media.image for media in product.media.all()]
    variant_img_paths = [media.image for media in variant.media.all()]
    product_media_paths = [media.image.name for media in product.media.all()]
    variant_media_paths = [media.image.name for media in variant.media.all()]
    images = product_img_paths + variant_img_paths

    variables = {"id": node_id}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )

    # then
    content = get_graphql_content(response)
    data = content["data"]["productDelete"]
    assert data["product"]["name"] == product.name
    with pytest.raises(product._meta.model.DoesNotExist):
        product.refresh_from_db()
    assert node_id == data["product"]["id"]

    assert delete_from_storage_task_mock.call_count == len(images)
    assert {
        call_args.args[0] for call_args in delete_from_storage_task_mock.call_args_list
    } == set(product_media_paths + variant_media_paths)
    mocked_recalculate_orders_task.assert_not_called()


@freeze_time("1914-06-28 10:50")
@patch("saleor.plugins.webhook.plugin.get_webhooks_for_event")
@patch("saleor.plugins.webhook.plugin.trigger_webhooks_async")
@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_product_trigger_webhook(
    mocked_recalculate_orders_task,
    mocked_webhook_trigger,
    mocked_get_webhooks_for_event,
    any_webhook,
    staff_api_client,
    product,
    permission_manage_products,
    settings,
):
    mocked_get_webhooks_for_event.return_value = [any_webhook]
    settings.PLUGINS = ["saleor.plugins.webhook.plugin.WebhookPlugin"]

    query = DELETE_PRODUCT_MUTATION
    node_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productDelete"]
    assert data["product"]["name"] == product.name
    with pytest.raises(product._meta.model.DoesNotExist):
        product.refresh_from_db()
    assert node_id == data["product"]["id"]
    mocked_webhook_trigger.assert_called_once_with(
        None,
        WebhookEventAsyncType.PRODUCT_DELETED,
        [any_webhook],
        product,
        SimpleLazyObject(lambda: staff_api_client.user),
        legacy_data_generator=ANY,
        allow_replica=False,
    )
    assert isinstance(
        mocked_webhook_trigger.call_args.kwargs["legacy_data_generator"], partial
    )
    mocked_recalculate_orders_task.assert_not_called()


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_product_with_file_attribute(
    mocked_recalculate_orders_task,
    staff_api_client,
    product,
    permission_manage_products,
    file_attribute,
):
    query = DELETE_PRODUCT_MUTATION
    product_type = product.product_type
    product_type.product_attributes.add(file_attribute)
    existing_value = file_attribute.values.first()
    associate_attribute_values_to_instance(
        product, {file_attribute.pk: [existing_value]}
    )

    node_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productDelete"]
    assert data["product"]["name"] == product.name
    with pytest.raises(product._meta.model.DoesNotExist):
        product.refresh_from_db()
    assert node_id == data["product"]["id"]
    mocked_recalculate_orders_task.assert_not_called()
    with pytest.raises(existing_value._meta.model.DoesNotExist):
        existing_value.refresh_from_db()


def test_delete_product_removes_checkout_lines(
    staff_api_client,
    checkout_with_items,
    permission_manage_products,
    settings,
):
    query = DELETE_PRODUCT_MUTATION
    checkout = checkout_with_items
    line = checkout.lines.first()
    product = line.variant.product
    node_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productDelete"]
    assert data["product"]["name"] == product.name

    with pytest.raises(product._meta.model.DoesNotExist):
        product.refresh_from_db()

    with pytest.raises(line._meta.model.DoesNotExist):
        line.refresh_from_db()
    assert checkout.lines.all().exists()

    checkout.refresh_from_db()

    assert node_id == data["product"]["id"]


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_product_variant_in_draft_order(
    mocked_recalculate_orders_task,
    staff_api_client,
    product_with_two_variants,
    permission_manage_products,
    order_list,
    channel_USD,
):
    query = DELETE_PRODUCT_MUTATION
    product = product_with_two_variants

    not_draft_order = order_list[1]
    draft_order = order_list[0]
    draft_order.status = OrderStatus.DRAFT
    draft_order.save(update_fields=["status"])

    draft_order_lines_pks = []
    not_draft_order_lines_pks = []
    for variant in product.variants.all():
        variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
        net = variant.get_price(variant_channel_listing)
        gross = Money(amount=net.amount, currency=net.currency)
        unit_price = TaxedMoney(net=net, gross=gross)
        quantity = 3
        total_price = unit_price * quantity

        order_line = OrderLine.objects.create(
            variant=variant,
            order=draft_order,
            product_name=str(variant.product),
            variant_name=str(variant),
            product_sku=variant.sku,
            product_variant_id=variant.get_global_id(),
            is_shipping_required=variant.is_shipping_required(),
            is_gift_card=variant.is_gift_card(),
            unit_price=TaxedMoney(net=net, gross=gross),
            total_price=total_price,
            quantity=quantity,
        )
        draft_order_lines_pks.append(order_line.pk)

        order_line_not_draft = OrderLine.objects.create(
            variant=variant,
            order=not_draft_order,
            product_name=str(variant.product),
            variant_name=str(variant),
            product_sku=variant.sku,
            product_variant_id=variant.get_global_id(),
            is_shipping_required=variant.is_shipping_required(),
            is_gift_card=variant.is_gift_card(),
            unit_price=TaxedMoney(net=net, gross=gross),
            total_price=total_price,
            quantity=quantity,
        )
        not_draft_order_lines_pks.append(order_line_not_draft.pk)

    node_id = graphene.Node.to_global_id("Product", product.id)
    variables = {"id": node_id}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productDelete"]
    assert data["product"]["name"] == product.name
    with pytest.raises(product._meta.model.DoesNotExist):
        product.refresh_from_db()
    assert node_id == data["product"]["id"]

    assert not OrderLine.objects.filter(pk__in=draft_order_lines_pks).exists()

    assert OrderLine.objects.filter(pk__in=not_draft_order_lines_pks).exists()
    mocked_recalculate_orders_task.assert_called_once_with([draft_order.id])

    event = OrderEvent.objects.filter(
        type=OrderEvents.ORDER_LINE_PRODUCT_DELETED
    ).last()
    assert event
    assert event.order == draft_order
    assert event.user == staff_api_client.user
    expected_params = [
        {
            "item": str(line),
            "line_pk": line.pk,
            "quantity": line.quantity,
        }
        for line in draft_order.lines.all()
    ]
    for param in expected_params:
        assert param in event.parameters


def test_product_delete_removes_reference_to_product(
    staff_api_client,
    product_type_product_reference_attribute,
    product_list,
    product_type,
    permission_manage_products,
):
    # given
    query = DELETE_PRODUCT_MUTATION

    product = product_list[0]
    product_ref = product_list[1]

    product_type.product_attributes.add(product_type_product_reference_attribute)
    attr_value = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        name=product_ref.name,
        slug=f"{product.pk}_{product_ref.pk}",
        reference_product=product_ref,
    )
    associate_attribute_values_to_instance(
        product, {product_type_product_reference_attribute.pk: [attr_value]}
    )

    reference_id = graphene.Node.to_global_id("Product", product_ref.pk)

    variables = {"id": reference_id}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productDelete"]

    with pytest.raises(attr_value._meta.model.DoesNotExist):
        attr_value.refresh_from_db()
    with pytest.raises(product_ref._meta.model.DoesNotExist):
        product_ref.refresh_from_db()

    assert not data["errors"]


def test_product_delete_removes_reference_to_product_variant(
    staff_api_client,
    variant,
    product_type_product_reference_attribute,
    permission_manage_products,
    product_list,
):
    query = DELETE_PRODUCT_MUTATION
    product_type = variant.product.product_type
    product_type.variant_attributes.set([product_type_product_reference_attribute])

    attr_value = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        name=product_list[0].name,
        slug=f"{variant.pk}_{product_list[0].pk}",
        reference_product=product_list[0],
    )

    associate_attribute_values_to_instance(
        variant, {product_type_product_reference_attribute.pk: [attr_value]}
    )
    reference_id = graphene.Node.to_global_id("Product", product_list[0].pk)

    variables = {"id": reference_id}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productDelete"]

    with pytest.raises(attr_value._meta.model.DoesNotExist):
        attr_value.refresh_from_db()
    with pytest.raises(product_list[0]._meta.model.DoesNotExist):
        product_list[0].refresh_from_db()

    assert not data["errors"]


def test_product_delete_removes_reference_to_page(
    staff_api_client,
    permission_manage_products,
    page,
    page_type_product_reference_attribute,
    product,
):
    query = DELETE_PRODUCT_MUTATION

    page_type = page.page_type
    page_type.page_attributes.add(page_type_product_reference_attribute)

    attr_value = AttributeValue.objects.create(
        attribute=page_type_product_reference_attribute,
        name=page.title,
        slug=f"{page.pk}_{product.pk}",
        reference_product=product,
    )
    associate_attribute_values_to_instance(
        page, {page_type_product_reference_attribute.pk: [attr_value]}
    )

    reference_id = graphene.Node.to_global_id("Product", product.pk)

    variables = {"id": reference_id}

    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productDelete"]

    with pytest.raises(attr_value._meta.model.DoesNotExist):
        attr_value.refresh_from_db()
    with pytest.raises(product._meta.model.DoesNotExist):
        product.refresh_from_db()

    assert not data["errors"]


DELETE_PRODUCT_BY_EXTERNAL_REFERENCE = """
    mutation DeleteProduct($id: ID, $externalReference: String) {
        productDelete(id: $id, externalReference: $externalReference) {
            product {
                id
                externalReference
            }
            errors {
                field
                message
            }
        }
    }
"""


@patch("saleor.order.tasks.recalculate_orders_task.delay")
def test_delete_product_by_external_reference(
    mocked_recalculate_orders_task,
    staff_api_client,
    product,
    permission_manage_products,
):
    # given
    query = DELETE_PRODUCT_BY_EXTERNAL_REFERENCE
    product.external_reference = "test-ext-id"
    product.save(update_fields=["external_reference"])
    variables = {"externalReference": product.external_reference}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["productDelete"]

    # then
    with pytest.raises(product._meta.model.DoesNotExist):
        product.refresh_from_db()
    assert (
        graphene.Node.to_global_id(product._meta.model.__name__, product.id)
        == data["product"]["id"]
    )
    assert data["product"]["externalReference"] == product.external_reference
    mocked_recalculate_orders_task.assert_not_called()


def test_delete_product_by_both_id_and_external_reference(
    staff_api_client, permission_manage_products
):
    # given
    query = DELETE_PRODUCT_BY_EXTERNAL_REFERENCE
    variables = {"externalReference": "whatever", "id": "whatever"}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productDelete"]["errors"]
    assert (
        errors[0]["message"]
        == "Argument 'id' cannot be combined with 'external_reference'"
    )


def test_delete_product_by_external_reference_not_existing(
    staff_api_client, permission_manage_products
):
    # given
    query = DELETE_PRODUCT_BY_EXTERNAL_REFERENCE
    ext_ref = "non-existing-ext-ref"
    variables = {"externalReference": ext_ref}

    # when
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)

    # then
    errors = content["data"]["productDelete"]["errors"]
    assert errors[0]["message"] == f"Couldn't resolve to a node: {ext_ref}"
