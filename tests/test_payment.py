from prices import Price

from saleor.order.models import Payment


def test_get_purchased_items(order_with_items, settings, voucher):

    payment = Payment.objects.create(order=order_with_items, variant='paypal')
    discount = Price('10.0', currency=settings.DEFAULT_CURRENCY)

    assert len(payment.get_purchased_items()) == len(order_with_items.get_items())

    for p, o in zip(payment.get_purchased_items(), order_with_items.get_items()):
        assert p.sku == o.product_sku
        assert p.quantity == o.quantity

    order_with_items.discount_name = 'Test'
    order_with_items.discount_amount = discount
    order_with_items.voucher = voucher
    order_with_items.save()

    settings.PAYMENT_VARIANTS = { 'paypal': ('PaypalProvider', {})}

    assert len(payment.get_purchased_items()) == len(order_with_items.get_items()) + 1

    for p, o in zip(payment.get_purchased_items()[:-1], order_with_items.get_items()):
        assert p.sku == o.product_sku
        assert p.quantity == o.quantity

    discounted = payment.get_purchased_items()[-1]

    assert discounted.name == order_with_items.discount_name
    assert discounted.sku == 'DISCOUNT'
    assert discounted.price == -1 * order_with_items.discount_amount.net
    assert discounted.quantity == 1
