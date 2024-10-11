import pytest
from django_countries import countries
from prices import Money

from ... import DiscountValueType, VoucherType
from ...models import Voucher, VoucherChannelListing, VoucherCode, VoucherCustomer


@pytest.fixture
def voucher_without_channel(db):
    voucher = Voucher.objects.create()
    VoucherCode.objects.create(code="mirumee", voucher=voucher)
    return voucher


@pytest.fixture
def voucher(voucher_without_channel, channel_USD):
    VoucherChannelListing.objects.create(
        voucher=voucher_without_channel,
        channel=channel_USD,
        discount=Money(20, channel_USD.currency_code),
    )
    return voucher_without_channel


@pytest.fixture
def voucher_with_many_codes(voucher):
    VoucherCode.objects.bulk_create(
        [
            VoucherCode(code="Multi1", voucher=voucher),
            VoucherCode(code="Multi2", voucher=voucher),
            VoucherCode(code="Multi3", voucher=voucher),
            VoucherCode(code="Multi4", voucher=voucher),
        ]
    )
    return voucher


@pytest.fixture
def voucher_with_many_channels(voucher, channel_PLN):
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_PLN,
        discount=Money(80, channel_PLN.currency_code),
    )
    return voucher


@pytest.fixture
def voucher_percentage(channel_USD):
    voucher = Voucher.objects.create(
        discount_value_type=DiscountValueType.PERCENTAGE,
    )
    VoucherCode.objects.create(code="saleor", voucher=voucher)
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount_value=10,
        currency=channel_USD.currency_code,
    )
    return voucher


@pytest.fixture
def voucher_specific_product_type(voucher_percentage, product):
    voucher_percentage.products.add(product)
    voucher_percentage.type = VoucherType.SPECIFIC_PRODUCT
    voucher_percentage.save()
    return voucher_percentage


@pytest.fixture
def voucher_with_high_min_spent_amount(channel_USD):
    voucher = Voucher.objects.create()
    VoucherCode.objects.create(code="mirumee", voucher=voucher)
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(10, channel_USD.currency_code),
        min_spent_amount=1_000_000,
    )
    return voucher


@pytest.fixture
def voucher_shipping_type(channel_USD):
    voucher = Voucher.objects.create(type=VoucherType.SHIPPING, countries="IS")
    VoucherCode.objects.create(code="mirumee", voucher=voucher)
    VoucherChannelListing.objects.create(
        voucher=voucher,
        channel=channel_USD,
        discount=Money(10, channel_USD.currency_code),
    )
    return voucher


@pytest.fixture
def voucher_free_shipping(voucher_percentage, channel_USD):
    voucher_percentage.type = VoucherType.SHIPPING
    voucher_percentage.name = "Free shipping"
    voucher_percentage.save()
    voucher_percentage.channel_listings.filter(channel=channel_USD).update(
        discount_value=100
    )
    return voucher_percentage


@pytest.fixture
def voucher_customer(voucher, customer_user):
    email = customer_user.email
    code = voucher.codes.first()
    return VoucherCustomer.objects.create(voucher_code=code, customer_email=email)


@pytest.fixture
def voucher_multiple_use(voucher_with_many_codes):
    voucher = voucher_with_many_codes
    voucher.usage_limit = 3
    voucher.save(update_fields=["usage_limit"])
    codes = voucher.codes.all()
    for code in codes:
        code.used = 1
    VoucherCode.objects.bulk_update(codes, ["used"])
    voucher.refresh_from_db()
    return voucher


@pytest.fixture
def voucher_single_use(voucher_with_many_codes):
    voucher = voucher_with_many_codes
    voucher.single_use = True
    voucher.save(update_fields=["single_use"])
    return voucher


@pytest.fixture
def voucher_with_many_channels_and_countries(voucher_with_many_channels):
    voucher_with_many_channels.countries = countries
    voucher_with_many_channels.save(update_fields=["countries"])
    return voucher_with_many_channels


@pytest.fixture
def voucher_list(channel_USD):
    [voucher_1, voucher_2, voucher_3] = Voucher.objects.bulk_create(
        [
            Voucher(),
            Voucher(),
            Voucher(),
        ]
    )

    VoucherCode.objects.bulk_create(
        [
            VoucherCode(code="voucher-1", voucher=voucher_1),
            VoucherCode(code="voucher-2", voucher=voucher_1),
            VoucherCode(code="voucher-3", voucher=voucher_2),
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


@pytest.fixture
def vouchers_list(channel_USD, channel_PLN):
    vouchers = Voucher.objects.bulk_create(
        [
            Voucher(name="Voucher1"),
            Voucher(name="Voucher2"),
            Voucher(name="Voucher3"),
        ]
    )
    VoucherCode.objects.bulk_create(
        [
            VoucherCode(code="Voucher1", voucher=vouchers[0]),
            VoucherCode(code="Voucher2", voucher=vouchers[1]),
            VoucherCode(code="Voucher3", voucher=vouchers[2]),
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
