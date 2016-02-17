from __future__ import unicode_literals

from django.core.urlresolvers import reverse
import pytest

from ...product.test_product import product_in_stock  # NOQA


@pytest.mark.integration
@pytest.mark.django_db
def test_stock_record_update_works(admin_client, product_in_stock):
    variant = product_in_stock.variants.get()
    stock = variant.stock.order_by('-quantity_allocated').first()
    quantity = stock.quantity
    quantity_allocated = stock.quantity_allocated
    url = reverse(
        'dashboard:product-stock-update', kwargs={
            'product_pk': product_in_stock.pk,
            'stock_pk': stock.pk})
    admin_client.post(url, {
        'variant': stock.variant_id, 'location': stock.location,
        'cost_price': stock.cost_price.net,
        'quantity': quantity + 5})
    new_stock = variant.stock.get(pk=stock.pk)
    assert new_stock.quantity == quantity + 5
    assert new_stock.quantity_allocated == quantity_allocated
