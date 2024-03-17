from unittest.mock import patch

import graphene
import pytest
from prices import Money, TaxedMoney

from .....attribute.utils import associate_attribute_values_to_instance
from .....order import OrderStatus
from .....order.models import OrderLine
from ....tests.utils import get_graphql_content

PRODUCT_TYPE_DELETE_MUTATION = """
    mutation deleteProductType($id: ID!) {
        productTypeDelete(id: $id) {
            productType {
                name
            }
        }
    }
"""


def test_product_type_delete_mutation(
    staff_api_client, product_type, permission_manage_product_types_and_attributes
):
    query = PRODUCT_TYPE_DELETE_MUTATION
    variables = {"id": graphene.Node.to_global_id("ProductType", product_type.id)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeDelete"]
    assert data["productType"]["name"] == product_type.name
    with pytest.raises(product_type._meta.model.DoesNotExist):
        product_type.refresh_from_db()


@patch("saleor.product.signals.delete_from_storage_task.delay")
def test_product_type_delete_mutation_deletes_also_images(
    delete_from_storage_task_mock,
    staff_api_client,
    product_type,
    product_with_image,
    permission_manage_product_types_and_attributes,
):
    query = PRODUCT_TYPE_DELETE_MUTATION
    product_type.products.add(product_with_image)
    media_obj = product_with_image.media.first()
    media_path = media_obj.image.name
    variables = {"id": graphene.Node.to_global_id("ProductType", product_type.id)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeDelete"]
    assert data["productType"]["name"] == product_type.name
    with pytest.raises(product_type._meta.model.DoesNotExist):
        product_type.refresh_from_db()
    delete_from_storage_task_mock.assert_called_once_with(media_path)
    with pytest.raises(product_with_image._meta.model.DoesNotExist):
        product_with_image.refresh_from_db()


def test_product_type_delete_with_file_attributes(
    staff_api_client,
    product_with_variant_with_file_attribute,
    file_attribute,
    permission_manage_product_types_and_attributes,
):
    query = PRODUCT_TYPE_DELETE_MUTATION
    product_type = product_with_variant_with_file_attribute.product_type

    product_type.product_attributes.add(file_attribute)
    associate_attribute_values_to_instance(
        product_with_variant_with_file_attribute,
        {file_attribute.pk: [file_attribute.values.last()]},
    )
    values = list(file_attribute.values.all())

    variables = {"id": graphene.Node.to_global_id("ProductType", product_type.id)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeDelete"]
    assert data["productType"]["name"] == product_type.name
    with pytest.raises(product_type._meta.model.DoesNotExist):
        product_type.refresh_from_db()
    for value in values:
        with pytest.raises(value._meta.model.DoesNotExist):
            value.refresh_from_db()
    with pytest.raises(
        product_with_variant_with_file_attribute._meta.model.DoesNotExist
    ):
        product_with_variant_with_file_attribute.refresh_from_db()


def test_product_type_delete_mutation_variants_in_draft_order(
    staff_api_client,
    permission_manage_product_types_and_attributes,
    product,
    order_list,
    channel_USD,
):
    query = PRODUCT_TYPE_DELETE_MUTATION
    product_type = product.product_type

    variant = product.variants.first()

    order_not_draft = order_list[-1]
    draft_order = order_list[1]
    draft_order.status = OrderStatus.DRAFT
    draft_order.save(update_fields=["status"])

    variant_channel_listing = variant.channel_listings.get(channel=channel_USD)
    net = variant.get_price(variant_channel_listing)
    gross = Money(amount=net.amount, currency=net.currency)
    quantity = 3
    unit_price = TaxedMoney(net=net, gross=gross)
    total_price = unit_price * quantity

    order_line_not_in_draft = OrderLine.objects.create(
        variant=variant,
        order=order_not_draft,
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        product_variant_id=variant.get_global_id(),
        is_shipping_required=variant.is_shipping_required(),
        is_gift_card=variant.is_gift_card(),
        unit_price=TaxedMoney(net=net, gross=gross),
        total_price=total_price,
        quantity=3,
    )

    order_line_in_draft = OrderLine.objects.create(
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
        quantity=3,
    )

    variables = {"id": graphene.Node.to_global_id("ProductType", product_type.id)}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_product_types_and_attributes]
    )
    content = get_graphql_content(response)
    data = content["data"]["productTypeDelete"]
    assert data["productType"]["name"] == product_type.name
    with pytest.raises(product_type._meta.model.DoesNotExist):
        product_type.refresh_from_db()

    with pytest.raises(order_line_in_draft._meta.model.DoesNotExist):
        order_line_in_draft.refresh_from_db()

    assert OrderLine.objects.filter(pk=order_line_not_in_draft.pk).exists()
