from typing import TYPE_CHECKING, Optional

from ...account.models import Address
from ...channel.models import Channel

if TYPE_CHECKING:
    from ...graphql.account.types import AddressInput


def get_active_country(
    channel: "Channel",
    shipping_address: Optional["Address"] = None,
    billing_address: Optional["Address"] = None,
    address_data: Optional["AddressInput"] = None,
):
    """Get country code for orders, checkouts and tax calculations.

    For checkouts and orders, there are following rules for determining the country
    code that should be used for tax calculations:
    - use country code from shipping address if it's provided in the first place
    - use country code from billing address if shipping address is not provided
    - if both shipping and billing addresses are not provided use the default country
    from channel

    To get country code from address data from mutation input use address_data parameter
    """
    if address_data is not None:
        return address_data.country

    if shipping_address:
        return shipping_address.country.code

    if billing_address:
        return billing_address.country.code

    return channel.default_country.code
