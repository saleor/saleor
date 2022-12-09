from unittest.mock import MagicMock

import graphene
from django.core.files import File
from prices import Money

from .....thumbnail.models import Thumbnail
from .....warehouse.models import Stock
from ....core.enums import ThumbnailFormatEnum
from ....tests.utils import get_graphql_content


def test_order_line_query(staff_api_client, permission_manage_orders, fulfilled_order):
    order = fulfilled_order
    query = """
        query OrdersQuery {
            orders(first: 1) {
                edges {
                    node {
                        lines {
                            thumbnail(size: 540) {
                                url
                            }
                            variant {
                                id
                            }
                            quantity
                            allocations {
                                id
                                quantity
                                warehouse {
                                    id
                                }
                            }
                            unitPrice {
                                currency
                                gross {
                                    amount
                                }
                            }
                            totalPrice {
                                currency
                                gross {
                                    amount
                                }
                            }
                            metadata {
                                key
                                value
                            }
                            privateMetadata {
                                key
                                value
                            }
                            taxClass {
                                name
                            }
                            taxClassName
                            taxClassMetadata {
                                key
                                value
                            }
                            taxClassPrivateMetadata {
                                key
                                value
                            }
                            taxRate
                        }
                    }
                }
            }
        }
    """
    line = order.lines.first()

    metadata_key = "md key"
    metadata_value = "md value"

    line.store_value_in_private_metadata({metadata_key: metadata_value})
    line.store_value_in_metadata({metadata_key: metadata_value})
    line.save()

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    first_order_data_line = order_data["lines"][0]
    variant_id = graphene.Node.to_global_id("ProductVariant", line.variant.pk)

    assert first_order_data_line["thumbnail"] is None
    assert first_order_data_line["variant"]["id"] == variant_id
    assert first_order_data_line["quantity"] == line.quantity
    assert first_order_data_line["unitPrice"]["currency"] == line.unit_price.currency
    assert first_order_data_line["metadata"] == [
        {"key": metadata_key, "value": metadata_value}
    ]
    assert first_order_data_line["privateMetadata"] == [
        {"key": metadata_key, "value": metadata_value}
    ]
    expected_unit_price = Money(
        amount=str(first_order_data_line["unitPrice"]["gross"]["amount"]),
        currency="USD",
    )
    assert first_order_data_line["totalPrice"]["currency"] == line.unit_price.currency
    assert expected_unit_price == line.unit_price.gross

    expected_total_price = Money(
        amount=str(first_order_data_line["totalPrice"]["gross"]["amount"]),
        currency="USD",
    )
    assert expected_total_price == line.unit_price.gross * line.quantity

    allocation = line.allocations.first()
    allocation_id = graphene.Node.to_global_id("Allocation", allocation.pk)
    warehouse_id = graphene.Node.to_global_id(
        "Warehouse", allocation.stock.warehouse.pk
    )
    assert first_order_data_line["allocations"] == [
        {
            "id": allocation_id,
            "quantity": allocation.quantity_allocated,
            "warehouse": {"id": warehouse_id},
        }
    ]

    line_tax_class = line.variant.product.tax_class
    assert first_order_data_line["taxClass"]["name"] == line_tax_class.name
    assert first_order_data_line["taxClassName"] == line_tax_class.name
    assert (
        first_order_data_line["taxClassMetadata"][0]["key"]
        == list(line_tax_class.metadata.keys())[0]
    )
    assert (
        first_order_data_line["taxClassMetadata"][0]["value"]
        == list(line_tax_class.metadata.values())[0]
    )
    assert (
        first_order_data_line["taxClassPrivateMetadata"][0]["key"]
        == list(line_tax_class.private_metadata.keys())[0]
    )
    assert (
        first_order_data_line["taxClassPrivateMetadata"][0]["value"]
        == list(line_tax_class.private_metadata.values())[0]
    )


def test_denormalized_tax_class_in_orderline_query(
    staff_api_client, permission_manage_orders, fulfilled_order
):
    # given
    order = fulfilled_order
    query = """
            query OrdersQuery {
                orders(first: 1) {
                    edges {
                        node {
                            lines {
                                thumbnail(size: 540) {
                                    url
                                }
                                variant {
                                    id
                                }
                                quantity
                                allocations {
                                    id
                                    quantity
                                    warehouse {
                                        id
                                    }
                                }
                                unitPrice {
                                    currency
                                    gross {
                                        amount
                                    }
                                }
                                totalPrice {
                                    currency
                                    gross {
                                        amount
                                    }
                                }
                                metadata {
                                    key
                                    value
                                }
                                privateMetadata {
                                    key
                                    value
                                }
                                taxClass {
                                    name
                                }
                                taxClassName
                                taxClassMetadata {
                                    key
                                    value
                                }
                                taxClassPrivateMetadata {
                                    key
                                    value
                                }
                                taxRate
                            }
                        }
                    }
                }
            }
        """

    staff_api_client.user.user_permissions.add(permission_manage_orders)
    line_tax_class = order.lines.first().tax_class
    assert line_tax_class

    # when
    line_tax_class.delete()
    response = staff_api_client.post_graphql(query)
    content = get_graphql_content(response)

    # then
    line_data = content["data"]["orders"]["edges"][0]["node"]["lines"][0]
    assert line_data["taxClass"] is None
    assert line_data["taxClassName"] == line_tax_class.name
    assert (
        line_data["taxClassMetadata"][0]["key"]
        == list(line_tax_class.metadata.keys())[0]
    )
    assert (
        line_data["taxClassMetadata"][0]["value"]
        == list(line_tax_class.metadata.values())[0]
    )
    assert (
        line_data["taxClassPrivateMetadata"][0]["key"]
        == list(line_tax_class.private_metadata.keys())[0]
    )
    assert (
        line_data["taxClassPrivateMetadata"][0]["value"]
        == list(line_tax_class.private_metadata.values())[0]
    )


def test_order_line_with_allocations(
    staff_api_client,
    permission_manage_orders,
    order_with_lines,
):
    # given
    order = order_with_lines
    query = """
        query OrdersQuery {
            orders(first: 1) {
                edges {
                    node {
                        lines {
                            id
                            allocations {
                                id
                                quantity
                                warehouse {
                                    id
                                }
                            }
                        }
                    }
                }
            }
        }
    """
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(query)

    # then
    content = get_graphql_content(response)
    lines = content["data"]["orders"]["edges"][0]["node"]["lines"]

    for line in lines:
        _, _id = graphene.Node.from_global_id(line["id"])
        order_line = order.lines.get(pk=_id)
        allocations_from_query = {
            allocation["quantity"] for allocation in line["allocations"]
        }
        allocations_from_db = set(
            order_line.allocations.values_list("quantity_allocated", flat=True)
        )
        assert allocations_from_query == allocations_from_db


QUERY_ORDER_LINE_STOCKS = """
query OrderQuery($id: ID!) {
    order(id: $id) {
        number
        lines {
            id
            quantity
            quantityFulfilled
            variant {
                id
                name
                sku
                stocks {
                    warehouse {
                        id
                        name
                    }
                }
            }
        }
    }
}
"""


def test_query_order_line_stocks(
    staff_api_client,
    permission_manage_orders,
    order_with_lines_for_cc,
    warehouse,
    warehouse_for_cc,
):
    """Ensure that stocks for normal and click and collect warehouses are returned."""
    # given
    order = order_with_lines_for_cc
    variant = order.lines.first().variant
    variables = {"id": graphene.Node.to_global_id("Order", order.id)}

    # create the variant stock for not click and collect warehouse
    Stock.objects.create(warehouse=warehouse, product_variant=variant, quantity=10)

    # when
    response = staff_api_client.post_graphql(
        QUERY_ORDER_LINE_STOCKS, variables, permissions=(permission_manage_orders,)
    )

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["order"]
    assert order_data
    assert len(order_data["lines"]) == 1
    assert {
        stock["warehouse"]["name"]
        for stock in order_data["lines"][0]["variant"]["stocks"]
    } == {warehouse.name, warehouse_for_cc.name}


ORDERS_QUERY_LINE_THUMBNAIL = """
    query OrdersQuery($size: Int, $format: ThumbnailFormatEnum) {
        orders(first: 1) {
            edges {
                node {
                    lines {
                        id
                        thumbnail(size: $size, format: $format) {
                            url
                        }
                    }
                }
            }
        }
    }
"""


def test_order_query_no_thumbnail(
    staff_api_client,
    permission_manage_orders,
    order_line,
):
    # given
    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_LINE_THUMBNAIL)

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert len(order_data["lines"]) == 1
    assert not order_data["lines"][0]["thumbnail"]


def test_order_query_product_image_size_and_format_given_proxy_url_returned(
    staff_api_client,
    permission_manage_orders,
    order_line,
    product_with_image,
    site_settings,
):
    # given
    order_line.variant.product = product_with_image
    media = product_with_image.media.first()
    format = ThumbnailFormatEnum.WEBP.name
    variables = {
        "size": 120,
        "format": format,
    }

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_LINE_THUMBNAIL, variables)

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    media_id = graphene.Node.to_global_id("ProductMedia", media.pk)
    domain = site_settings.site.domain
    assert len(order_data["lines"]) == 1
    assert (
        order_data["lines"][0]["thumbnail"]["url"]
        == f"http://{domain}/thumbnail/{media_id}/128/{format.lower()}/"
    )


def test_order_query_product_image_size_given_proxy_url_returned(
    staff_api_client,
    permission_manage_orders,
    order_line,
    product_with_image,
    site_settings,
):
    # given
    order_line.variant.product = product_with_image
    media = product_with_image.media.first()
    variables = {
        "size": 120,
    }

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_LINE_THUMBNAIL, variables)

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    media_id = graphene.Node.to_global_id("ProductMedia", media.pk)
    assert len(order_data["lines"]) == 1
    assert (
        order_data["lines"][0]["thumbnail"]["url"]
        == f"http://{site_settings.site.domain}/thumbnail/{media_id}/128/"
    )


def test_order_query_product_image_size_given_thumbnail_url_returned(
    staff_api_client,
    permission_manage_orders,
    order_line,
    product_with_image,
    site_settings,
):
    # given
    order_line.variant.product = product_with_image
    media = product_with_image.media.first()

    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    Thumbnail.objects.create(product_media=media, size=128, image=thumbnail_mock)

    variables = {
        "size": 120,
    }

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_LINE_THUMBNAIL, variables)

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert len(order_data["lines"]) == 1
    assert (
        order_data["lines"][0]["thumbnail"]["url"]
        == f"http://{site_settings.site.domain}/media/thumbnails/{thumbnail_mock.name}"
    )


def test_order_query_variant_image_size_and_format_given_proxy_url_returned(
    staff_api_client,
    permission_manage_orders,
    order_line,
    variant_with_image,
    site_settings,
):
    # given
    order_line.variant = variant_with_image
    media = variant_with_image.media.first()
    format = ThumbnailFormatEnum.WEBP.name
    variables = {
        "size": 120,
        "format": format,
    }

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_LINE_THUMBNAIL, variables)

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    media_id = graphene.Node.to_global_id("ProductMedia", media.pk)
    domain = site_settings.site.domain
    assert len(order_data["lines"]) == 1
    assert (
        order_data["lines"][0]["thumbnail"]["url"]
        == f"http://{domain}/thumbnail/{media_id}/128/{format.lower()}/"
    )


def test_order_query_variant_image_size_given_proxy_url_returned(
    staff_api_client,
    permission_manage_orders,
    order_line,
    variant_with_image,
    site_settings,
):
    # given
    order_line.variant = variant_with_image
    media = variant_with_image.media.first()
    variables = {
        "size": 120,
    }

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_LINE_THUMBNAIL, variables)

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    media_id = graphene.Node.to_global_id("ProductMedia", media.pk)
    assert len(order_data["lines"]) == 1
    assert (
        order_data["lines"][0]["thumbnail"]["url"]
        == f"http://{site_settings.site.domain}/thumbnail/{media_id}/128/"
    )


def test_order_query_variant_image_size_given_thumbnail_url_returned(
    staff_api_client,
    permission_manage_orders,
    order_line,
    variant_with_image,
    site_settings,
):
    # given
    order_line.variant = variant_with_image
    media = variant_with_image.media.first()

    thumbnail_mock = MagicMock(spec=File)
    thumbnail_mock.name = "thumbnail_image.jpg"
    Thumbnail.objects.create(product_media=media, size=128, image=thumbnail_mock)

    variables = {
        "size": 120,
    }

    staff_api_client.user.user_permissions.add(permission_manage_orders)

    # when
    response = staff_api_client.post_graphql(ORDERS_QUERY_LINE_THUMBNAIL, variables)

    # then
    content = get_graphql_content(response)
    order_data = content["data"]["orders"]["edges"][0]["node"]
    assert len(order_data["lines"]) == 1
    assert (
        order_data["lines"][0]["thumbnail"]["url"]
        == f"http://{site_settings.site.domain}/media/thumbnails/{thumbnail_mock.name}"
    )
