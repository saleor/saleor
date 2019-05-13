import graphene
import pytest

from saleor.discount.models import Sale, Voucher
from saleor.menu.models import Menu
from saleor.order import OrderStatus
from saleor.product.models import (
    Attribute,
    AttributeValue,
    Category,
    ProductType,
    ProductVariant,
)
from saleor.shipping.models import ShippingMethod, ShippingZone

from .utils import assert_read_only_mode

MUTATION_DELETE_ORDER_LINES = """
    mutation draftOrderLinesBulkDelete($ids: [ID]!) {
        draftOrderLinesBulkDelete(ids: $ids) {
            count
            errors {
                field
                message
            }
        }
    }
    """


@pytest.fixture
def attribute_list():
    attribute_1 = Attribute.objects.create(slug="size", name="Size")
    attribute_2 = Attribute.objects.create(slug="weight", name="Weight")
    attribute_3 = Attribute.objects.create(slug="thickness", name="Thickness")
    return attribute_1, attribute_2, attribute_3


@pytest.fixture
def attribute_value_list(color_attribute):
    value_1 = AttributeValue.objects.create(
        slug="pink", name="Pink", attribute=color_attribute, value="#FF69B4"
    )
    value_2 = AttributeValue.objects.create(
        slug="white", name="White", attribute=color_attribute, value="#FFFFFF"
    )
    value_3 = AttributeValue.objects.create(
        slug="black", name="Black", attribute=color_attribute, value="#000000"
    )
    return value_1, value_2, value_3


@pytest.fixture
def category_list():
    category_1 = Category.objects.create(name="Category 1", slug="category-1")
    category_2 = Category.objects.create(name="Category 2", slug="category-2")
    category_3 = Category.objects.create(name="Category 3", slug="category-3")
    return category_1, category_2, category_3


@pytest.fixture
def menu_list():
    menu_1 = Menu.objects.create(name="test-navbar-1", json_content={})
    menu_2 = Menu.objects.create(name="test-navbar-2", json_content={})
    menu_3 = Menu.objects.create(name="test-navbar-3", json_content={})
    return menu_1, menu_2, menu_3


@pytest.fixture
def product_type_list():
    product_type_1 = ProductType.objects.create(name="Type 1")
    product_type_2 = ProductType.objects.create(name="Type 2")
    product_type_3 = ProductType.objects.create(name="Type 3")
    return product_type_1, product_type_2, product_type_3


@pytest.fixture
def product_variant_list(product):
    product_variant_1 = ProductVariant.objects.create(product=product, sku="1")
    product_variant_2 = ProductVariant.objects.create(product=product, sku="2")
    product_variant_3 = ProductVariant.objects.create(product=product, sku="3")
    return product_variant_1, product_variant_2, product_variant_3


@pytest.fixture
def sale_list():
    sale_1 = Sale.objects.create(name="Sale 1", value=5)
    sale_2 = Sale.objects.create(name="Sale 2", value=5)
    sale_3 = Sale.objects.create(name="Sale 3", value=5)
    return sale_1, sale_2, sale_3


@pytest.fixture
def shipping_method_list(shipping_zone):
    shipping_method_1 = ShippingMethod.objects.create(
        shipping_zone=shipping_zone, name="DHL"
    )
    shipping_method_2 = ShippingMethod.objects.create(
        shipping_zone=shipping_zone, name="DPD"
    )
    shipping_method_3 = ShippingMethod.objects.create(
        shipping_zone=shipping_zone, name="GLS"
    )
    return shipping_method_1, shipping_method_2, shipping_method_3


@pytest.fixture
def shipping_zone_list():
    shipping_zone_1 = ShippingZone.objects.create(name="Europe")
    shipping_zone_2 = ShippingZone.objects.create(name="Asia")
    shipping_zone_3 = ShippingZone.objects.create(name="Oceania")
    return shipping_zone_1, shipping_zone_2, shipping_zone_3


@pytest.fixture
def voucher_list():
    voucher_1 = Voucher.objects.create(code="voucher-1", discount_value=1)
    voucher_2 = Voucher.objects.create(code="voucher-2", discount_value=2)
    voucher_3 = Voucher.objects.create(code="voucher-3", discount_value=3)
    return voucher_1, voucher_2, voucher_3


def test_delete_attributes(
    staff_api_client, attribute_list, permission_manage_products
):
    query = """
    mutation attributeBulkDelete($ids: [ID]!) {
        attributeBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [
            graphene.Node.to_global_id("Attribute", attr.id) for attr in attribute_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    assert_read_only_mode(response)


def test_delete_attribute_values(
    staff_api_client, attribute_value_list, permission_manage_products
):
    query = """
    mutation attributeValueBulkDelete($ids: [ID]!) {
        attributeValueBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [
            graphene.Node.to_global_id("AttributeValue", val.id)
            for val in attribute_value_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    assert_read_only_mode(response)


def test_delete_categories(staff_api_client, category_list, permission_manage_products):
    query = """
    mutation categoryBulkDelete($ids: [ID]!) {
        categoryBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [
            graphene.Node.to_global_id("Category", category.id)
            for category in category_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    assert_read_only_mode(response)


def test_delete_collections(
    staff_api_client, collection_list, permission_manage_products
):
    query = """
    mutation collectionBulkDelete($ids: [ID]!) {
        collectionBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [
            graphene.Node.to_global_id("Collection", collection.id)
            for collection in collection_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    assert_read_only_mode(response)


def test_delete_customers(staff_api_client, user_list, permission_manage_users):
    user_1, user_2, *users = user_list

    query = """
    mutation customerBulkDelete($ids: [ID]!) {
        customerBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [graphene.Node.to_global_id("User", user.id) for user in user_list]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users]
    )
    assert_read_only_mode(response)


def test_delete_draft_orders(staff_api_client, order_list, permission_manage_orders):
    order_1, order_2, *orders = order_list
    order_1.status = OrderStatus.DRAFT
    order_2.status = OrderStatus.DRAFT
    order_1.save()
    order_2.save()

    query = """
    mutation draftOrderBulkDelete($ids: [ID]!) {
        draftOrderBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [graphene.Node.to_global_id("Order", order.id) for order in order_list]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders]
    )
    assert_read_only_mode(response)


def test_fail_to_delete_non_draft_order_lines(
    staff_api_client, order_with_lines, permission_manage_orders
):
    order = order_with_lines
    order_lines = [line for line in order]
    # Ensure we cannot delete a non-draft order
    order.status = OrderStatus.CANCELED
    order.save()

    variables = {
        "ids": [
            graphene.Node.to_global_id("OrderLine", order_line.id)
            for order_line in order_lines
        ]
    }
    response = staff_api_client.post_graphql(
        MUTATION_DELETE_ORDER_LINES, variables, permissions=[permission_manage_orders]
    )
    assert_read_only_mode(response)


def test_delete_draft_order_lines(
    staff_api_client, order_with_lines, permission_manage_orders
):
    order = order_with_lines
    order_lines = [line for line in order]
    # Only lines in draft order can be deleted
    order.status = OrderStatus.DRAFT
    order.save()

    variables = {
        "ids": [
            graphene.Node.to_global_id("OrderLine", order_line.id)
            for order_line in order_lines
        ]
    }

    response = staff_api_client.post_graphql(
        MUTATION_DELETE_ORDER_LINES, variables, permissions=[permission_manage_orders]
    )
    assert_read_only_mode(response)


def test_delete_menus(staff_api_client, menu_list, permission_manage_menus):
    query = """
    mutation menuBulkDelete($ids: [ID]!) {
        menuBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [
            graphene.Node.to_global_id("Menu", collection.id)
            for collection in menu_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus]
    )
    assert_read_only_mode(response)


def test_delete_menu_items(staff_api_client, menu_item_list, permission_manage_menus):
    query = """
    mutation menuItemBulkDelete($ids: [ID]!) {
        menuItemBulkDelete(ids: $ids) {
            count
        }
    }
    """
    variables = {
        "ids": [
            graphene.Node.to_global_id("MenuItem", menu_item.id)
            for menu_item in menu_item_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus]
    )
    assert_read_only_mode(response)


def test_delete_empty_list_of_ids(staff_api_client, permission_manage_menus):
    query = """
    mutation menuItemBulkDelete($ids: [ID]!) {
        menuItemBulkDelete(ids: $ids) {
            count
        }
    }
    """
    menu_item_list = []
    variables = {"ids": menu_item_list}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus]
    )
    assert_read_only_mode(response)


def test_delete_pages(staff_api_client, page_list, permission_manage_pages):
    query = """
    mutation pageBulkDelete($ids: [ID]!) {
        pageBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [graphene.Node.to_global_id("Page", page.id) for page in page_list]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages]
    )
    assert_read_only_mode(response)


def test_delete_products(staff_api_client, product_list, permission_manage_products):
    query = """
    mutation productBulkDelete($ids: [ID]!) {
        productBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [
            graphene.Node.to_global_id("Product", product.id)
            for product in product_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    assert_read_only_mode(response)


def test_delete_product_images(
    staff_api_client, product_with_images, permission_manage_products
):
    images = product_with_images.images.all()

    query = """
    mutation productImageBulkDelete($ids: [ID]!) {
        productImageBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [
            graphene.Node.to_global_id("ProductImage", image.id) for image in images
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    assert_read_only_mode(response)


def test_delete_product_types(
    staff_api_client, product_type_list, permission_manage_products
):
    query = """
    mutation productTypeBulkDelete($ids: [ID]!) {
        productTypeBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [
            graphene.Node.to_global_id("ProductType", type.id)
            for type in product_type_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    assert_read_only_mode(response)


def test_delete_product_variants(
    staff_api_client, product_variant_list, permission_manage_products
):
    query = """
    mutation productVariantBulkDelete($ids: [ID]!) {
        productVariantBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [
            graphene.Node.to_global_id("ProductVariant", variant.id)
            for variant in product_variant_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products]
    )
    assert_read_only_mode(response)


def test_delete_sales(staff_api_client, sale_list, permission_manage_discounts):
    query = """
    mutation saleBulkDelete($ids: [ID]!) {
        saleBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [graphene.Node.to_global_id("Sale", sale.id) for sale in sale_list]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    assert_read_only_mode(response)


def test_delete_shipping_methods(
    staff_api_client, shipping_method_list, permission_manage_shipping
):
    query = """
    mutation shippingPriceBulkDelete($ids: [ID]!) {
        shippingPriceBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [
            graphene.Node.to_global_id("ShippingMethod", method.id)
            for method in shipping_method_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping]
    )
    assert_read_only_mode(response)


def test_delete_shipping_zones(
    staff_api_client, shipping_zone_list, permission_manage_shipping
):
    query = """
    mutation shippingZoneBulkDelete($ids: [ID]!) {
        shippingZoneBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [
            graphene.Node.to_global_id("ShippingZone", zone.id)
            for zone in shipping_zone_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping]
    )
    assert_read_only_mode(response)


def test_delete_staff_members(
    staff_api_client, user_list, permission_manage_staff, superuser
):
    *users, staff_1, staff_2 = user_list
    users.append(superuser)

    query = """
    mutation staffBulkDelete($ids: [ID]!) {
        staffBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [graphene.Node.to_global_id("User", user.id) for user in user_list]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff]
    )
    assert_read_only_mode(response)


def test_delete_vouchers(staff_api_client, voucher_list, permission_manage_discounts):
    query = """
    mutation voucherBulkDelete($ids: [ID]!) {
        voucherBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {
        "ids": [
            graphene.Node.to_global_id("Voucher", voucher.id)
            for voucher in voucher_list
        ]
    }
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts]
    )
    assert_read_only_mode(response)
