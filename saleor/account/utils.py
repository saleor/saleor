from ..checkout import AddressType


def get_user_addresses(user):
    if not user:
        return None
    if user.organization:
        return user.organization.addresses
    return user.addresses


def get_user_default_address(user, address_type):
    if address_type == AddressType.BILLING:
        if user.organization:
            return user.organization.default_billing_address
        return user.default_billing_address

    elif address_type == AddressType.SHIPPING:
        return user.default_shipping_address

    raise ValueError("Unrecognized AddressType: %s" % address_type)


def get_user_default_shipping_address(user):
    return get_user_default_address(user, AddressType.SHIPPING)


def get_user_default_billing_address(user):
    return get_user_default_address(user, AddressType.BILLING)


def set_user_default_address(user, address, address_type):
    """ Sets the correct default address, taking into account whether
    or not the user is associated with a organization. Returns the object that
    was updated (user or organization)."""
    if address_type == AddressType.BILLING:
        prop = 'default_billing_address'
        obj = user.organization or user
    elif address_type == AddressType.SHIPPING:
        prop = 'default_shipping_address'
        obj = user

    setattr(obj, prop, address)
    obj.save(update_fields=[prop])
    return obj


def store_user_address(user, address, address_type):
    """Add address to user address book and set as default one."""
    user_addresses = get_user_addresses(user)
    address, _ = user_addresses.get_or_create(**address.as_data())

    if address_type == AddressType.BILLING:
        if not user.default_billing_address:
            set_user_default_address(user, address, address_type)
    elif address_type == AddressType.SHIPPING:
        if not user.default_shipping_address:
            set_user_default_address(user, address, address_type)
