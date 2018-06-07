from django.shortcuts import reverse
from tests.utils import get_graphql_content


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
