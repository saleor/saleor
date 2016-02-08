from satchless.item import InsufficientStock


def contains_unavailable_products(cart):
    try:
        [item.product.check_quantity(item.quantity) for item in cart]
    except InsufficientStock:
        return True
    return False


def remove_unavailable_products(cart):
    for item in cart:
        try:
            cart.add(item.product, quantity=item.quantity, replace=True)
        except InsufficientStock as e:
            quantity = e.item.get_stock_quantity()
            cart.add(item.product, quantity=quantity, replace=True)


def get_product_variants_and_prices(cart, product):
    lines = (cart_line for cart_line in cart
             if cart_line.product.product_id == product.id)
    for line in lines:
        for i in range(line.quantity):
            yield line.product, line.get_price_per_item()


def get_category_variants_and_prices(cart, discounted_category):
    products = set((cart_line.product.product for cart_line in cart))
    discounted_products = []
    for product in products:
        for category in product.categories.all():
            is_descendant = category.is_descendant_of(
                discounted_category, include_self=True)
            if is_descendant:
                discounted_products.append(product)
    for product in discounted_products:
        for line in get_product_variants_and_prices(cart, product):
            yield line
