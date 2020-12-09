import graphene
import pytest

from ....discount.models import Sale, SaleChannelListing, Voucher, VoucherChannelListing
from ...tests.utils import get_graphql_content


@pytest.fixture
def sale_list(channel_USD):
    sales = Sale.objects.bulk_create(
        [Sale(name="Sale 1"), Sale(name="Sale 2"), Sale(name="Sale 3")]
    )
    SaleChannelListing.objects.bulk_create(
        [
            SaleChannelListing(sale=sale, discount_value=5, channel=channel_USD)
            for sale in sales
        ]
    )
    return list(sales)


@pytest.fixture
def voucher_list(channel_USD):
    [voucher_1, voucher_2, voucher_3] = Voucher.objects.bulk_create(
        [
            Voucher(code="voucher-1"),
            Voucher(code="voucher-2"),
            Voucher(code="voucher-3"),
        ]
    )
    VoucherChannelListing.objects.bulk_create(
        [
            VoucherChannelListing(
                voucher=voucher_1,
                channel=channel_USD,
                discount_value=1,
                currency=channel_USD.currency_code,
            ),
            VoucherChannelListing(
                voucher=voucher_2,
                channel=channel_USD,
                discount_value=2,
                currency=channel_USD.currency_code,
            ),
            VoucherChannelListing(
                voucher=voucher_3,
                channel=channel_USD,
                discount_value=3,
                currency=channel_USD.currency_code,
            ),
        ]
    )
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
