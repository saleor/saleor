import graphene
import pytest

from ....discount.models import Sale, Voucher
from ...tests.utils import get_graphql_content


@pytest.fixture
def sale_list():
    sale_1 = Sale.objects.create(name="Sale 1", value=5)
    sale_2 = Sale.objects.create(name="Sale 2", value=5)
    sale_3 = Sale.objects.create(name="Sale 3", value=5)
    return sale_1, sale_2, sale_3


@pytest.fixture
def voucher_list():
    voucher_1 = Voucher.objects.create(code="voucher-1", discount_value=1)
    voucher_2 = Voucher.objects.create(code="voucher-2", discount_value=2)
    voucher_3 = Voucher.objects.create(code="voucher-3", discount_value=3)
    return voucher_1, voucher_2, voucher_3


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
    content = get_graphql_content(response)

    assert content["data"]["saleBulkDelete"]["count"] == 3
    assert not Sale.objects.filter(id__in=[sale.id for sale in sale_list]).exists()


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
    content = get_graphql_content(response)

    assert content["data"]["voucherBulkDelete"]["count"] == 3
    assert not Voucher.objects.filter(
        id__in=[voucher.id for voucher in voucher_list]
    ).exists()
