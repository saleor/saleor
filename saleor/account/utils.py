from ..checkout import AddressType
from ..core.demo_obfuscators import obfuscate_address


def store_user_address(user, address, address_type):
    """Add address to user address book and set as default one."""
    address, _ = user.addresses.get_or_create(**address.as_data())

    # DEMO: obfuscate user address
    address = obfuscate_address(address)

    if address_type == AddressType.BILLING:
        if not user.default_billing_address:
            user.default_billing_address = address
            user.save(update_fields=['default_billing_address'])
    elif address_type == AddressType.SHIPPING:
        if not user.default_shipping_address:
            user.default_shipping_address = address
            user.save(update_fields=['default_shipping_address'])
