from satchless.item import InsufficientStock


def has_available_products(cart):
    try:
        [item.product.check_quantity(item.quantity) for item in cart]
    except InsufficientStock:
        return False
    return True


def remove_unavailable_products(cart):
    for item in cart:
        try:
            cart.add(item.product, quantity=item.quantity, replace=True)
        except InsufficientStock as e:
            quantity = e.item.get_stock_quantity()
            cart.add(item.product, quantity=quantity, replace=True)
    return cart
