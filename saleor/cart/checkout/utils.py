def save_billing_address_in_cart(cart, address):
    """Save billing address in cart if changed.

    Remove previously saved address if not connected to any user.
    """
    has_address_changed = (
        not address and cart.billing_address or
        address and not cart.billing_address or
        address and cart.billing_address and address != cart.billing_address)
    if has_address_changed:
        remove_old_address = (
            cart.billing_address and (not cart.user or (
                cart.user and
                cart.billing_address not in cart.user.addresses.all())))
        if remove_old_address:
            cart.billing_address.delete()
        cart.billing_address = address
        cart.save()


def save_shipping_address_in_cart(cart, address):
    """Save shipping address in cart if changed.

    Remove previously saved address if not connected to any user.
    """
    has_address_changed = (
        not address and cart.shipping_address or
        address and not cart.shipping_address or
        address and cart.shipping_address and address != cart.shipping_address)
    if has_address_changed:
        remove_old_address = (
            cart.shipping_address and (not cart.user or (
                cart.user and
                cart.shipping_address not in cart.user.addresses.all())))
        if remove_old_address:
            cart.shipping_address.delete()
        cart.shipping_address = address
        cart.save()


def get_checkout_data(cart, discounts, taxes):
    """Data shared between views in checkout process."""
    lines = [
        (line, line.get_total(discounts, taxes)) for line in cart.lines.all()]
    subtotal = cart.get_total(discounts, taxes)
    shipping_price = cart.get_shipping_price(taxes)
    return {
        'cart': cart,
        'cart_are_taxes_handled': bool(taxes),
        'cart_lines': lines,
        'cart_subtotal': subtotal,
        'cart_shipping_price': shipping_price}
