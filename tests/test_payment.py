from decimal import Decimal

from prices import Money

from saleor.order.models import Payment


def test_get_purchased_items(order_with_lines, settings, voucher):
    payment = Payment.objects.create(order=order_with_lines, variant='paypal')
    discount = Money('10.0', settings.DEFAULT_CURRENCY)

    assert len(payment.get_purchased_items()) == order_with_lines.lines.count()

    for p, o in zip(
            payment.get_purchased_items(), order_with_lines.lines.all()):
        assert p.sku == o.product_sku
        assert p.quantity == o.quantity
        assert p.price == o.unit_price_net.quantize(Decimal('0.01')).amount
        assert p.currency == o.unit_price.currency

    order_with_lines.discount_name = 'Test'
    order_with_lines.discount_amount = discount
    order_with_lines.voucher = voucher
    order_with_lines.save()

    settings.PAYMENT_VARIANTS = {'paypal': ('PaypalProvider', {})}

    assert len(payment.get_purchased_items()) == (
        order_with_lines.lines.count() + 1)

    for p, o in zip(
            payment.get_purchased_items()[:-1], order_with_lines.lines.all()):
        assert p.sku == o.product_sku
        assert p.quantity == o.quantity
        assert p.price == o.unit_price_net.quantize(Decimal('0.01')).amount
        assert p.currency == o.unit_price.currency

    discounted = payment.get_purchased_items()[-1]

    assert discounted.name == order_with_lines.discount_name
    assert discounted.sku == 'DISCOUNT'
    assert discounted.price == -1 * order_with_lines.discount_amount.amount
    assert discounted.currency == order_with_lines.discount_amount.currency
    assert discounted.quantity == 1
