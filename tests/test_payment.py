from prices import Price

from saleor.order.models import Payment


def test_get_purchased_items_and_discounts(order_with_items, settings, voucher):
    settings.PAYMENT_VARIANTS = {'paypal': ('PaypalProvider', {})}

    payment = Payment.objects.create(order=order_with_items, variant='paypal')
    discount = Price('10.0', currency=settings.DEFAULT_CURRENCY)
    payment_items = payment.get_purchased_items()

    order_with_items.discount_name = 'Test'
    order_with_items.discount_amount = discount
    order_with_items.voucher = voucher
    order_with_items.save()
    assert len(payment_items) == len(order_with_items.get_items())

    pairs = zip(payment_items, order_with_items.get_items())
    for payment_item, order_item in pairs:
        assert payment_item.sku == order_item.product_sku
        assert payment_item.quantity == order_item.quantity

    discounted = payment.get_discounts()[0]
    assert discounted.name == order_with_items.discount_name
    assert discounted.amount == order_with_items.discount_amount.net
