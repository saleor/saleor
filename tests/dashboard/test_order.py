from __future__ import unicode_literals

import pytest
from django.urls import reverse
from saleor.order.models import Order, OrderHistoryEntry, OrderedItem, DeliveryGroup
from saleor.product.models import Stock
from tests.utils import get_redirect_location


@pytest.mark.integration
@pytest.mark.django_db
def test_view_cancel_order_line(admin_client, order_with_items_and_stock):
    lines_before = order_with_items_and_stock.get_items()
    lines_before_count = lines_before.count()
    line = lines_before.first()
    line_quantity = line.quantity
    quantity_allocated_before = line.stock.quantity_allocated
    product = line.product

    url = reverse(
        'dashboard:orderline-cancel', kwargs={
            'order_pk': order_with_items_and_stock.pk,
            'line_pk': line.pk})

    response = admin_client.get(url)
    assert response.status_code == 200
    response = admin_client.post(url, {'csrfmiddlewaretoken': 'hello'})
    assert response.status_code == 302
    assert get_redirect_location(response) == reverse(
        'dashboard:order-details', args=[order_with_items_and_stock.pk])
    # check ordered item removal
    lines_after = Order.objects.get().get_items()
    assert lines_before_count - 1 == lines_after.count()
    # check stock deallocation
    assert Stock.objects.first().quantity_allocated == quantity_allocated_before - line_quantity
    # check note in the order's history
    OrderHistoryEntry.objects.get(
        order=order_with_items_and_stock).message = 'Cancelled item %s' % product
    url = reverse(
        'dashboard:orderline-cancel', kwargs={
            'order_pk': order_with_items_and_stock.pk,
            'line_pk': OrderedItem.objects.get().pk})
    response = admin_client.post(
        url, {'csrfmiddlewaretoken': 'hello'}, follow=True)
    # check delivery group removal if it becomes empty
    assert Order.objects.get().get_items().count() == 0
    assert DeliveryGroup.objects.count() == 0
    # check success messages after redirect
    assert response.context['messages']
