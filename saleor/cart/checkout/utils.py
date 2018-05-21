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
            cart.user and cart.shipping_address and
            cart.shipping_address not in cart.user.addresses.all())
        if remove_old_address:
            cart.shipping_address.delete()
        cart.shipping_address = address
        cart.save()


def get_checkout_data(cart, discounts, taxes):
    """Data shared between views in checkout process."""
    lines = [
        (line, line.get_total(discounts, taxes)) for line in cart.lines.all()]
    subtotal = cart.get_total(discounts, taxes)
    return {
        'cart': cart,
        'cart_lines': lines,
        'cart_subtotal': subtotal}
