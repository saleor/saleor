import pytest

from .....discount.models import Voucher, VoucherChannelListing
from ....tests.utils import get_graphql_content


@pytest.fixture
def vouchers_list(channel_USD, channel_PLN):
    vouchers = Voucher.objects.bulk_create(
        [
            Voucher(name="Voucher1", code="Voucher1"),
            Voucher(name="Voucher2", code="Voucher2"),
            Voucher(name="Voucher3", code="Voucher3"),
        ]
    )
    values = [15, 5, 25]
    voucher_channel_listings = []
    for voucher, value in zip(vouchers, values):
        voucher_channel_listings.append(
            VoucherChannelListing(
                voucher=voucher,
                channel=channel_USD,
                discount_value=value,
                currency=channel_USD.currency_code,
            )
        )
        voucher_channel_listings.append(
            VoucherChannelListing(
                voucher=voucher,
                channel=channel_PLN,
                discount_value=value * 2,
                currency=channel_PLN.currency_code,
            )
        )
    VoucherChannelListing.objects.bulk_create(voucher_channel_listings)
    return vouchers


VOUCHERS_QUERY = """
query GetVouchers($channel: String){
  vouchers(last: 10, channel: $channel) {
    edges {
      node {
        id
        name
        type
        startDate
        endDate
        usageLimit
        code
        applyOncePerOrder
        applyOncePerCustomer
        discountValueType
        minCheckoutItemsQuantity
        countries{
          code
          country
          vat{
            countryCode
            standardRate
          }
        }
        categories(first: 10) {
          edges {
            node {
              id
            }
          }
        }
        collections(first: 10) {
          edges {
            node {
              id
            }
          }
        }
        products(first: 10) {
          edges {
            node {
              id
            }
          }
        }
        channelListings {
          id
          discountValue
          currency
          minSpent{
            currency
            amount
          }
          channel {
            id
            name
            isActive
            slug
            currencyCode
          }
        }
        discountValue
        currency
      }
    }
  }
}
"""


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_vouchers_query_with_channel_slug(
    staff_api_client,
    vouchers_list,
    channel_USD,
    permission_manage_discounts,
    count_queries,
):
    variables = {"channel": channel_USD.slug}
    get_graphql_content(
        staff_api_client.post_graphql(
            VOUCHERS_QUERY,
            variables,
            permissions=[permission_manage_discounts],
            check_no_permissions=False,
        )
    )


@pytest.mark.django_db
@pytest.mark.count_queries(autouse=False)
def test_vouchers_query_withot_channel_slug(
    staff_api_client,
    vouchers_list,
    permission_manage_discounts,
    count_queries,
):
    get_graphql_content(
        staff_api_client.post_graphql(
            VOUCHERS_QUERY,
            {},
            permissions=[permission_manage_discounts],
            check_no_permissions=False,
        )
    )
