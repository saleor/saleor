import graphene
import pytest

from saleor.account.models import User
from saleor.discount.models import Sale, Voucher
from saleor.menu.models import Menu, MenuItem
from saleor.order import OrderStatus, models as order_models
from saleor.page.models import Page
from saleor.product.models import (
    Attribute, AttributeValue, Category, Collection, Product, ProductImage,
    ProductType, ProductVariant)
from saleor.shipping.models import ShippingMethod, ShippingZone

from .utils import get_graphql_content

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
    attribute_1 = Attribute.objects.create(
        slug='size', name='Size')
    attribute_2 = Attribute.objects.create(
        slug='weight', name='Weight')
    attribute_3 = Attribute.objects.create(
        slug='thickness', name='Thickness')
    return attribute_1, attribute_2, attribute_3


@pytest.fixture
def attribute_value_list(color_attribute):
    value_1 = AttributeValue.objects.create(
        slug='pink', name='Pink', attribute=color_attribute, value='#FF69B4')
    value_2 = AttributeValue.objects.create(
        slug='white', name='White', attribute=color_attribute, value='#FFFFFF')
    value_3 = AttributeValue.objects.create(
        slug='black', name='Black', attribute=color_attribute, value='#000000')
    return value_1, value_2, value_3


@pytest.fixture
def category_list():
    category_1 = Category.objects.create(
        name='Category 1', slug='category-1')
    category_2 = Category.objects.create(
        name='Category 2', slug='category-2')
    category_3 = Category.objects.create(
        name='Category 3', slug='category-3')
    return category_1, category_2, category_3


@pytest.fixture
def menu_list():
    menu_1 = Menu.objects.create(name='test-navbar-1', json_content={})
    menu_2 = Menu.objects.create(name='test-navbar-2', json_content={})
    menu_3 = Menu.objects.create(name='test-navbar-3', json_content={})
    return menu_1, menu_2, menu_3


@pytest.fixture
def product_type_list():
    product_type_1 = ProductType.objects.create(name='Type 1')
    product_type_2 = ProductType.objects.create(name='Type 2')
    product_type_3 = ProductType.objects.create(name='Type 3')
    return product_type_1, product_type_2, product_type_3


@pytest.fixture
def product_variant_list(product):
    product_variant_1 = ProductVariant.objects.create(product=product, sku='1')
    product_variant_2 = ProductVariant.objects.create(product=product, sku='2')
    product_variant_3 = ProductVariant.objects.create(product=product, sku='3')
    return product_variant_1, product_variant_2, product_variant_3


@pytest.fixture
def sale_list():
    sale_1 = Sale.objects.create(name='Sale 1', value=5)
    sale_2 = Sale.objects.create(name='Sale 2', value=5)
    sale_3 = Sale.objects.create(name='Sale 3', value=5)
    return sale_1, sale_2, sale_3


@pytest.fixture
def shipping_method_list(shipping_zone):
    shipping_method_1 = ShippingMethod.objects.create(
        shipping_zone=shipping_zone, name='DHL')
    shipping_method_2 = ShippingMethod.objects.create(
        shipping_zone=shipping_zone, name='DPD')
    shipping_method_3 = ShippingMethod.objects.create(
        shipping_zone=shipping_zone, name='GLS')
    return shipping_method_1, shipping_method_2, shipping_method_3


@pytest.fixture
def shipping_zone_list():
    shipping_zone_1 = ShippingZone.objects.create(name='Europe')
    shipping_zone_2 = ShippingZone.objects.create(name='Asia')
    shipping_zone_3 = ShippingZone.objects.create(name='Oceania')
    return shipping_zone_1, shipping_zone_2, shipping_zone_3


@pytest.fixture
def voucher_list():
    voucher_1 = Voucher.objects.create(code='voucher-1', discount_value=1)
    voucher_2 = Voucher.objects.create(code='voucher-2', discount_value=2)
    voucher_3 = Voucher.objects.create(code='voucher-3', discount_value=3)
    return voucher_1, voucher_2, voucher_3


def test_delete_attributes(
        staff_api_client, attribute_list, permission_manage_products):
    query = """
    mutation attributeBulkDelete($ids: [ID]!) {
        attributeBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {'ids': [
        graphene.Node.to_global_id('Attribute', attr.id)
        for attr in attribute_list]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)

    assert content['data']['attributeBulkDelete']['count'] == 3
    assert not Attribute.objects.filter(
        id__in=[attr.id for attr in attribute_list]).exists()


def test_delete_attribute_values(
        staff_api_client, attribute_value_list, permission_manage_products):
    query = """
    mutation attributeValueBulkDelete($ids: [ID]!) {
        attributeValueBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {'ids': [
        graphene.Node.to_global_id('AttributeValue', val.id)
        for val in attribute_value_list]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)

    assert content['data']['attributeValueBulkDelete']['count'] == 3
    assert not AttributeValue.objects.filter(
        id__in=[val.id for val in attribute_value_list]).exists()


def test_delete_categories(
        staff_api_client, category_list, permission_manage_products):
    query = """
    mutation categoryBulkDelete($ids: [ID]!) {
        categoryBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {'ids': [
        graphene.Node.to_global_id('Category', category.id)
        for category in category_list]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)

    assert content['data']['categoryBulkDelete']['count'] == 3
    assert not Category.objects.filter(
        id__in=[category.id for category in category_list]).exists()


def test_delete_collections(
        staff_api_client, collection_list, permission_manage_products):
    query = """
    mutation collectionBulkDelete($ids: [ID]!) {
        collectionBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {'ids': [
        graphene.Node.to_global_id('Collection', collection.id)
        for collection in collection_list]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)

    assert content['data']['collectionBulkDelete']['count'] == 3
    assert not Collection.objects.filter(
        id__in=[collection.id for collection in collection_list]).exists()


def test_delete_customers(
        staff_api_client, user_list, permission_manage_users):
    user_1, user_2, *users = user_list

    query = """
    mutation customerBulkDelete($ids: [ID]!) {
        customerBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {'ids': [
        graphene.Node.to_global_id('User', user.id)
        for user in user_list]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_users])
    content = get_graphql_content(response)

    assert content['data']['customerBulkDelete']['count'] == 2
    assert not User.objects.filter(
        id__in=[user.id for user in [user_1, user_2]]).exists()
    assert User.objects.filter(
        id__in=[user.id for user in users]).count() == len(users)


def test_delete_draft_orders(
        staff_api_client, order_list, permission_manage_orders):
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

    variables = {'ids': [
        graphene.Node.to_global_id('Order', order.id)
        for order in order_list]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_orders])
    content = get_graphql_content(response)

    assert content['data']['draftOrderBulkDelete']['count'] == 2
    assert not order_models.Order.objects.filter(
        id__in=[order_1.id, order_2.id]).exists()
    assert order_models.Order.objects.filter(
        id__in=[order.id for order in orders]).count() == len(orders)


def test_fail_to_delete_non_draft_order_lines(
        staff_api_client, order_with_lines, permission_manage_orders):
    order = order_with_lines
    order_lines = [line for line in order]
    # Ensure we cannot delete a non-draft order
    order.status = OrderStatus.CANCELED
    order.save()

    variables = {'ids': [
        graphene.Node.to_global_id('OrderLine', order_line.id)
        for order_line in order_lines]}
    response = staff_api_client.post_graphql(
        MUTATION_DELETE_ORDER_LINES, variables,
        permissions=[permission_manage_orders])

    content = get_graphql_content(response)
    assert 'errors' in content['data']['draftOrderLinesBulkDelete']
    assert content['data']['draftOrderLinesBulkDelete']['count'] == 0


def test_delete_draft_order_lines(
        staff_api_client, order_with_lines, permission_manage_orders):
    order = order_with_lines
    order_lines = [line for line in order]
    # Only lines in draft order can be deleted
    order.status = OrderStatus.DRAFT
    order.save()

    variables = {'ids': [
        graphene.Node.to_global_id('OrderLine', order_line.id)
        for order_line in order_lines]}

    response = staff_api_client.post_graphql(
        MUTATION_DELETE_ORDER_LINES, variables,
        permissions=[permission_manage_orders])
    content = get_graphql_content(response)

    assert content['data']['draftOrderLinesBulkDelete']['count'] == 2
    assert not order_models.OrderLine.objects.filter(
        id__in=[order_line.pk for order_line in order_lines]).exists()


def test_delete_menus(
        staff_api_client, menu_list, permission_manage_menus):
    query = """
    mutation menuBulkDelete($ids: [ID]!) {
        menuBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {'ids': [
        graphene.Node.to_global_id('Menu', collection.id)
        for collection in menu_list]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus])
    content = get_graphql_content(response)

    assert content['data']['menuBulkDelete']['count'] == 3
    assert not Menu.objects.filter(
        id__in=[menu.id for menu in menu_list]).exists()


def test_delete_menu_items(
        staff_api_client, menu_item_list, permission_manage_menus):
    query = """
    mutation menuItemBulkDelete($ids: [ID]!) {
        menuItemBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {'ids': [
        graphene.Node.to_global_id('MenuItem', menu_item.id)
        for menu_item in menu_item_list]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_menus])
    content = get_graphql_content(response)

    assert content['data']['menuItemBulkDelete']['count'] == 3
    assert not MenuItem.objects.filter(
        id__in=[menu_item.id for menu_item in menu_item_list]).exists()


def test_delete_pages(
        staff_api_client, page_list, permission_manage_pages):
    query = """
    mutation pageBulkDelete($ids: [ID]!) {
        pageBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {'ids': [
        graphene.Node.to_global_id('Page', page.id)
        for page in page_list]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_pages])
    content = get_graphql_content(response)

    assert content['data']['pageBulkDelete']['count'] == len(page_list)
    assert not Page.objects.filter(
        id__in=[page.id for page in page_list]).exists()


def test_delete_products(
        staff_api_client, product_list, permission_manage_products):
    query = """
    mutation productBulkDelete($ids: [ID]!) {
        productBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {'ids': [
        graphene.Node.to_global_id('Product', product.id)
        for product in product_list]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)

    assert content['data']['productBulkDelete']['count'] == 3
    assert not Product.objects.filter(
        id__in=[product.id for product in product_list]).exists()


def test_delete_product_images(
        staff_api_client, product_with_images, permission_manage_products):
    images = product_with_images.images.all()

    query = """
    mutation productImageBulkDelete($ids: [ID]!) {
        productImageBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {'ids': [
        graphene.Node.to_global_id('ProductImage', image.id)
        for image in images]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)

    assert content['data']['productImageBulkDelete']['count'] == 2
    assert not ProductImage.objects.filter(
        id__in=[image.id for image in images]).exists()


def test_delete_product_types(
        staff_api_client, product_type_list, permission_manage_products):
    query = """
    mutation productTypeBulkDelete($ids: [ID]!) {
        productTypeBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {'ids': [
        graphene.Node.to_global_id('ProductType', type.id)
        for type in product_type_list]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)

    assert content['data']['productTypeBulkDelete']['count'] == 3
    assert not ProductType.objects.filter(
        id__in=[type.id for type in product_type_list]).exists()


def test_delete_product_variants(
        staff_api_client, product_variant_list, permission_manage_products):
    query = """
    mutation productVariantBulkDelete($ids: [ID]!) {
        productVariantBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {'ids': [
        graphene.Node.to_global_id('ProductVariant', variant.id)
        for variant in product_variant_list]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_products])
    content = get_graphql_content(response)

    assert content['data']['productVariantBulkDelete']['count'] == 3
    assert not ProductVariant.objects.filter(
        id__in=[variant.id for variant in product_variant_list]).exists()


def test_delete_sales(
        staff_api_client, sale_list, permission_manage_discounts):
    query = """
    mutation saleBulkDelete($ids: [ID]!) {
        saleBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {'ids': [
        graphene.Node.to_global_id('Sale', sale.id)
        for sale in sale_list]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts])
    content = get_graphql_content(response)

    assert content['data']['saleBulkDelete']['count'] == 3
    assert not Sale.objects.filter(
        id__in=[sale.id for sale in sale_list]).exists()


def test_delete_shipping_methods(
        staff_api_client, shipping_method_list, permission_manage_shipping):
    query = """
    mutation shippingPriceBulkDelete($ids: [ID]!) {
        shippingPriceBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {'ids': [
        graphene.Node.to_global_id('ShippingMethod', method.id)
        for method in shipping_method_list]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping])
    content = get_graphql_content(response)

    assert content['data']['shippingPriceBulkDelete']['count'] == 3
    assert not ShippingMethod.objects.filter(
        id__in=[method.id for method in shipping_method_list]).exists()


def test_delete_shipping_zones(
        staff_api_client, shipping_zone_list, permission_manage_shipping):
    query = """
    mutation shippingZoneBulkDelete($ids: [ID]!) {
        shippingZoneBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {'ids': [
        graphene.Node.to_global_id('ShippingZone', zone.id)
        for zone in shipping_zone_list]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_shipping])
    content = get_graphql_content(response)

    assert content['data']['shippingZoneBulkDelete']['count'] == 3
    assert not ShippingZone.objects.filter(
        id__in=[zone.id for zone in shipping_zone_list]).exists()


def test_delete_staff_members(
        staff_api_client, user_list, permission_manage_staff, superuser):
    *users, staff_1, staff_2 = user_list
    users.append(superuser)

    query = """
    mutation staffBulkDelete($ids: [ID]!) {
        staffBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {'ids': [
        graphene.Node.to_global_id('User', user.id)
        for user in user_list]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_staff])
    content = get_graphql_content(response)

    assert content['data']['staffBulkDelete']['count'] == 2
    assert not User.objects.filter(
        id__in=[user.id for user in [staff_1, staff_2]]).exists()
    assert User.objects.filter(
        id__in=[user.id for user in users]).count() == len(users)


def test_delete_vouchers(
        staff_api_client, voucher_list, permission_manage_discounts):
    query = """
    mutation voucherBulkDelete($ids: [ID]!) {
        voucherBulkDelete(ids: $ids) {
            count
        }
    }
    """

    variables = {'ids': [
        graphene.Node.to_global_id('Voucher', voucher.id)
        for voucher in voucher_list]}
    response = staff_api_client.post_graphql(
        query, variables, permissions=[permission_manage_discounts])
    content = get_graphql_content(response)

    assert content['data']['voucherBulkDelete']['count'] == 3
    assert not Voucher.objects.filter(
        id__in=[voucher.id for voucher in voucher_list]).exists()
