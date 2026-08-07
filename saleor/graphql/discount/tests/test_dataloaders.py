import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from prices import Money

from ....discount.models import NotApplicable, Voucher
from ...context import SaleorContext
from ..dataloaders import VoucherInfoByVoucherCodeLoader


def test_voucher_info_by_voucher_code_loader_loads_channel_listings(
    voucher, channel_USD
):
    # given
    code = voucher.codes.first().code
    context = SaleorContext()
    expected_listing_ids = set(voucher.channel_listings.values_list("id", flat=True))

    # when
    voucher_info = VoucherInfoByVoucherCodeLoader(context).load(code).get()

    # then
    assert voucher_info is not None
    assert voucher_info.voucher_code == code
    assert voucher_info.voucher.id == voucher.id
    assert {listing.id for listing in voucher_info.channel_listings} == (
        expected_listing_ids
    )
    assert {
        listing.id for listing in voucher_info.voucher.channel_listings.all()
    } == expected_listing_ids

    with CaptureQueriesContext(connection) as queries:
        discount = voucher_info.voucher.get_discount(
            channel_USD, channel_listings=voucher_info.channel_listings
        )
        assert discount(Money(100, channel_USD.currency_code)) == Money(
            80, channel_USD.currency_code
        )
    assert not any("channel" in query["sql"].lower() for query in queries)


def test_voucher_info_by_voucher_code_loader_unknown_code():
    # given
    context = SaleorContext()

    # when
    voucher_info = VoucherInfoByVoucherCodeLoader(context).load("unknown-code").get()

    # then
    assert voucher_info is None


def test_voucher_info_by_voucher_code_loader_batches_channel_listings(
    voucher, voucher_percentage, channel_USD
):
    # given
    codes = [
        voucher.codes.first().code,
        voucher_percentage.codes.first().code,
    ]
    context = SaleorContext()

    # when
    with CaptureQueriesContext(connection) as queries:
        voucher_infos = VoucherInfoByVoucherCodeLoader(context).load_many(codes).get()

    # then
    assert len(voucher_infos) == 2
    assert all(info is not None for info in voucher_infos)
    for voucher_info in voucher_infos:
        assert len(voucher_info.channel_listings) == 1
        voucher_info.voucher.get_discount(
            channel_USD, channel_listings=voucher_info.channel_listings
        )

    channel_listing_queries = [
        query["sql"]
        for query in queries
        if "discount_voucherchannellisting" in query["sql"].lower()
    ]
    assert len(channel_listing_queries) == 1


def test_voucher_get_discount_accepts_channel_listings(voucher, channel_USD):
    # given
    listings = list(voucher.channel_listings.all())
    voucher = Voucher.objects.get(pk=voucher.pk)

    # when
    with CaptureQueriesContext(connection) as queries:
        discount = voucher.get_discount(channel_USD, channel_listings=listings)
        discounted = discount(Money(50, channel_USD.currency_code))

    # then
    assert discounted == Money(30, channel_USD.currency_code)
    assert not any("channel" in query["sql"].lower() for query in queries)


def test_voucher_get_discount_with_channel_listings_not_assigned(
    voucher, channel_PLN
):
    # given
    listings = list(voucher.channel_listings.all())
    voucher = Voucher.objects.get(pk=voucher.pk)

    # when / then
    with CaptureQueriesContext(connection) as queries:
        with pytest.raises(NotApplicable):
            voucher.get_discount(channel_PLN, channel_listings=listings)
    assert not any("channel" in query["sql"].lower() for query in queries)


def test_voucher_get_discount_amount_for_with_channel_listings(voucher, channel_USD):
    # given
    listings = list(voucher.channel_listings.all())
    voucher = Voucher.objects.get(pk=voucher.pk)
    price = Money(50, channel_USD.currency_code)

    # when
    discount_amount = voucher.get_discount_amount_for(
        price, channel_USD, channel_listings=listings
    )

    # then
    assert discount_amount == Money(20, channel_USD.currency_code)
