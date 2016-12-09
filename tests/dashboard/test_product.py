from __future__ import unicode_literals

from django.core.urlresolvers import reverse
import pytest

from saleor.dashboard.product.forms import ProductClassForm
from saleor.product.models import ProductClass


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
        'variant': stock.variant_id, 'location': stock.location.id,
        'cost_price': stock.cost_price.net,
        'quantity': quantity + 5})
    new_stock = variant.stock.get(pk=stock.pk)
    assert new_stock.quantity == quantity + 5
    assert new_stock.quantity_allocated == quantity_allocated


def test_valid_product_class_form(color_attribute, size_attribute):
    data = {'name': "Testing Class",
            'product_attributes': [color_attribute.pk],
            'variant_attributes': [size_attribute.pk],
            'has_variants': True}
    form = ProductClassForm(data)
    assert form.is_valid()

    # Don't allow same attribute in both fields
    data['variant_attributes'] = [color_attribute.pk, size_attribute.pk]
    data['product_attributes'] = [size_attribute.pk]
    form = ProductClassForm(data)
    assert not form.is_valid()


def test_variantless_product_class_form(color_attribute, size_attribute):
    data = {'name': "Testing Class",
            'product_attributes': [color_attribute.pk],
            'variant_attributes': [],
            'has_variants': False}
    form = ProductClassForm(data)
    assert form.is_valid()

    # Don't allow variant attributes when no variants
    data = {'name': "Testing Class",
            'product_attributes': [color_attribute.pk],
            'variant_attributes': [size_attribute.pk],
            'has_variants': False}
    form = ProductClassForm(data)
    assert not form.is_valid()

