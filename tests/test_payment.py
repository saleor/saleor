from prices import Price

from saleor.order.models import Payment


def test_get_purchased_items(order_with_lines, settings, voucher):

    payment = Payment.objects.create(order=order_with_lines, variant='paypal')
    discount = Price('10.0', currency=settings.DEFAULT_CURRENCY)

    assert len(payment.get_purchased_items()) == len(
        order_with_lines.get_lines())

    for p, o in zip(
            payment.get_purchased_items(), order_with_lines.get_lines()):
        assert p.sku == o.product_sku
        assert p.quantity == o.quantity

    order_with_lines.discount_name = 'Test'
    order_with_lines.discount_amount = discount
    order_with_lines.voucher = voucher
    order_with_lines.save()

    settings.PAYMENT_VARIANTS = {'paypal': ('PaypalProvider', {})}

    assert len(payment.get_purchased_items()) == len(
        order_with_lines.get_lines()) + 1

    for p, o in zip(
            payment.get_purchased_items()[:-1], order_with_lines.get_lines()):
        assert p.sku == o.product_sku
        assert p.quantity == o.quantity

    discounted = payment.get_purchased_items()[-1]

    assert discounted.name == order_with_lines.discount_name
    assert discounted.sku == 'DISCOUNT'
    assert discounted.price == -1 * order_with_lines.discount_amount.net
    assert discounted.quantity == 1
