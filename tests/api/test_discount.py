import json

from django.shortcuts import reverse
from tests.utils import get_graphql_content

from saleor.discount import (
    DiscountValueType, VoucherApplyToProduct, VoucherType)


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
        $type: String, $name: String, $code: String, $applyTo: String
        $discountValueType: String, $discountValue: Decimal, $limit: Decimal) {
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
    variables = json.dumps(
        {
            'name': 'test voucher',
            'type': VoucherType.VALUE,
            'code': 'testcode123',
            'applyTo': VoucherApplyToProduct.ALL_PRODUCTS,
            'discountValueType': DiscountValueType.FIXED,
            'discountValue': "10.12",
            'limit': "1.12"
        }
    )
    response = admin_api_client.post(
        reverse('api'), {'query': query, 'variables': variables})
    content = get_graphql_content(response)
    assert 'errors' not in content
    data = content['data']['voucherCreate']['voucher']
    assert data['type'] == VoucherType.VALUE.upper()
    assert data['limit']['amount'] == float("1.12")
    assert data['applyTo'] == VoucherApplyToProduct.ALL_PRODUCTS
    assert data['name'] == 'test voucher'
    assert data['code'] == 'testcode123'
    assert data['discountValueType'] == DiscountValueType.FIXED.upper()
