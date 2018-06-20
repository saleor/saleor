import json

import graphene
import pytest
from django.shortcuts import reverse
from tests.utils import get_graphql_content

from saleor.discount import (
    DiscountValueType, VoucherApplyToProduct, VoucherType)
from saleor.graphql.discount.types import (
    ApplyToEnum, DiscountValueTypeEnum, VoucherTypeEnum)

from .utils import assert_no_permission


def test_voucher_permissions(
        staff_api_client, staff_group, staff_user, permission_view_voucher):
    query = """
    query vouchers{
        vouchers(first: 1) {
            edges {
                node {
                    name
                }
            }
        }
    }
    """
    # Query to ensure user with no permissions can't see vouchers
    response = staff_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    message = 'You do not have permission to perform this action'
    assert content['errors'][0]['message'] == message

    # Give staff user proper permissions
    staff_group.permissions.add(permission_view_voucher)
    staff_user.groups.add(staff_group)

    # Query again
    response = staff_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content


def test_voucher_query(
        admin_api_client, voucher):
    query = """
    query vouchers{
        vouchers(first: 1) {
            edges {
                node {
                    type
                    name
                    code
                    usageLimit
                    used
                    startDate
                    discountValueType
                    discountValue
                    applyTo
                }
            }
        }
    }
    """
    response = admin_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['vouchers']['edges'][0]['node']
    assert data['type'] == voucher.type.upper()
    assert data['name'] == voucher.name
    assert data['code'] == voucher.code
    assert data['usageLimit'] == voucher.usage_limit
    assert data['used'] == voucher.used
    assert data['startDate'] == voucher.start_date.isoformat()
    assert data['discountValueType'] == voucher.discount_value_type.upper()
    assert data['discountValue'] == voucher.discount_value
    assert data['applyTo'] == voucher.apply_to


def test_sale_query(
        admin_api_client, sale):
    query = """
        query sales{
            sales(first: 1) {
                edges {
                    node {
                        type
                        name
                        value
                    }
                }
            }
        }
        """
    response = admin_api_client.post(reverse('api'), {'query': query})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['sales']['edges'][0]['node']
    assert data['type'] == sale.type.upper()
    assert data['name'] == sale.name
    assert data['value'] == sale.value


def test_create_voucher(user_api_client, admin_api_client):
    query = """
    mutation  voucherCreate(
        $type: VoucherTypeEnum, $name: String, $code: String,
        $applyTo: ApplyToEnum, $discountValueType: DiscountValueTypeEnum,
        $discountValue: Decimal, $limit: Decimal) {
            voucherCreate(input: {
            name: $name, type: $type, code: $code, applyTo: $applyTo, 
            discountValueType: $discountValueType, discountValue: $discountValue,
            limit: $limit}) {
                errors {
                    field
                    message
                }
                voucher {
                    type
                    limit {
                        amount
                    }
                    applyTo
                    name
                    code
                    discountValueType
                }
            }
        }
    """
    variables = json.dumps({
        'name': 'test voucher',
        'type': VoucherTypeEnum.VALUE.name,
        'code': 'testcode123',
        'applyTo': ApplyToEnum.ALL_PRODUCTS.name,
        'discountValueType': DiscountValueTypeEnum.FIXED.name,
        'discountValue': '10.12',
        'limit': '1.12'})
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_no_permission(response)

    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['voucherCreate']['voucher']
    assert data['type'] == VoucherType.VALUE.upper()
    assert data['limit']['amount'] == float('1.12')
    assert data['applyTo'] == VoucherApplyToProduct.ALL_PRODUCTS
    assert data['name'] == 'test voucher'
    assert data['code'] == 'testcode123'
    assert data['discountValueType'] == DiscountValueType.FIXED.upper()


def test_update_voucher(user_api_client, admin_api_client, voucher):
    query = """
    mutation  voucherUpdate($code: String,
        $discountValueType: DiscountValueTypeEnum, $id: ID!) {
            voucherUpdate(id: $id, input: {
                code: $code, discountValueType: $discountValueType}) {
                errors {
                    field
                    message
                }
                voucher {
                    code
                    discountValueType
                }
            }
        }
    """
    # Set discount value type to 'fixed' and change it in mutation
    voucher.discount_value_type = DiscountValueType.FIXED
    voucher.save()
    assert voucher.code != 'testcode123'
    variables = json.dumps({
        'id': graphene.Node.to_global_id('Voucher', voucher.id),
        'code': 'testcode123',
        'discountValueType': DiscountValueTypeEnum.PERCENTAGE.name})

    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_no_permission(response)

    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['voucherUpdate']['voucher']
    assert data['code'] == 'testcode123'
    assert data['discountValueType'] == DiscountValueType.PERCENTAGE.upper()


def test_voucher_delete_mutation(user_api_client, admin_api_client, voucher):
    query = """
        mutation DeleteVoucher($id: ID!) {
            voucherDelete(id: $id) {
                voucher {
                    name
                    id
                }
                errors {
                    field
                    message
                }
              }
            }
    """
    variables = json.dumps({
        'id': graphene.Node.to_global_id('Voucher', voucher.id)})

    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_no_permission(response)

    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['voucherDelete']
    assert data['voucher']['name'] == voucher.name
    with pytest.raises(voucher._meta.model.DoesNotExist):
        voucher.refresh_from_db()


def test_create_sale(user_api_client, admin_api_client):
    query = """
    mutation  saleCreate(
        $type: DiscountValueTypeEnum, $name: String, $value: Decimal) {
            saleCreate(input: {name: $name, type: $type, value: $value}) {
                errors {
                    field
                    message
                }
                sale {
                    type
                    name
                    value
                }
            }
        }
    """
    variables = json.dumps({
        'name': 'test sale',
        'type': DiscountValueTypeEnum.FIXED.name,
        'value': '10.12'})
    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_no_permission(response)

    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['saleCreate']['sale']
    assert data['type'] == DiscountValueType.FIXED.upper()
    assert data['name'] == 'test sale'
    assert data['value'] == 10.12


def test_update_sale(user_api_client, admin_api_client, sale):
    query = """
    mutation  saleUpdate($type: DiscountValueTypeEnum, $id: ID!) {
            saleUpdate(id: $id, input: {type: $type}) {
                errors {
                    field
                    message
                }
                sale {
                    type
                }
            }
        }
    """
    # Set discount value type to 'fixed' and change it in mutation
    sale.type = DiscountValueType.FIXED
    sale.save()
    variables = json.dumps({
        'id': graphene.Node.to_global_id('Sale', sale.id),
        'type': DiscountValueTypeEnum.PERCENTAGE.name})

    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})

    assert_no_permission(response)

    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['saleUpdate']['sale']
    assert data['type'] == DiscountValueType.PERCENTAGE.upper()


def test_sale_delete_mutation(user_api_client, admin_api_client, sale):
    query = """
        mutation DeleteSale($id: ID!) {
            saleDelete(id: $id) {
                sale {
                    name
                    id
                }
                errors {
                    field
                    message
                }
              }
            }
    """
    variables = json.dumps({
        'id': graphene.Node.to_global_id('Sale', sale.id)})

    response = user_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    assert_no_permission(response)

    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['saleDelete']
    assert data['sale']['name'] == sale.name
    with pytest.raises(sale._meta.model.DoesNotExist):
        sale.refresh_from_db()


def test_validate_voucher(voucher, admin_api_client, product):
    query = """
    mutation  voucherUpdate(
        $product_id: ID, $id: ID!, $type: VoucherTypeEnum) {
            voucherUpdate(
            id: $id, input: {product: $product_id, type: $type}) {
                errors {
                    field
                    message
                }
                voucher {
                    product {
                        name
                    }
                }
            }
        }
    """

    assert not voucher.product
    variables = json.dumps({
        'type': VoucherTypeEnum.PRODUCT.name,
        'id': graphene.Node.to_global_id('Voucher', voucher.id),
        'product': graphene.Node.to_global_id('Product', product.id)})

    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    data = content['data']['voucherUpdate']['errors'][0]
    assert data['field'] == 'product'
    assert data['message'] == 'This field is required.'
