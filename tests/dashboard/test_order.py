from __future__ import unicode_literals

import mock
import pytest
from django.core.urlresolvers import reverse
from saleor.dashboard.order.forms import ChangeQuantityForm, MoveItemsForm
from saleor.order.models import (Order, OrderHistoryEntry, OrderedItem,
                                 DeliveryGroup)
from saleor.order.utils import add_items_to_delivery_group
from saleor.product.models import Stock, ProductVariant
from tests.utils import get_redirect_location, get_url_path


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
    assert OrderHistoryEntry.objects.get(
        order=order_with_items_and_stock).comment == 'Cancelled item %s' % product
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


@pytest.mark.integration
@pytest.mark.django_db
def test_view_change_order_line_quantity(admin_client, order_with_items_and_stock):
    """
    user goes to order details page
    user selects first order line with quantity 3 and changes it to 2
    """
    lines_before_quantity_change = order_with_items_and_stock.get_items()
    lines_before_quantity_change_count = lines_before_quantity_change.count()
    line = lines_before_quantity_change.first()
    line_quantity_before_quantity_change = line.quantity

    url = reverse(
        'dashboard:orderline-change-quantity', kwargs={
            'order_pk': order_with_items_and_stock.pk,
            'line_pk': line.pk})
    response = admin_client.get(url)
    assert response.status_code == 200
    response = admin_client.post(
        url, {'quantity': 2}, follow=True)
    redirected_to, redirect_status_code = response.redirect_chain[-1]
    # check redirection
    assert redirect_status_code == 302
    assert get_url_path(redirected_to) == reverse(
        'dashboard:order-details',
        args=[order_with_items_and_stock.pk])
    # success messages should appear after redirect
    assert response.context['messages']
    lines_after = Order.objects.get().get_items()
    # order should have the same lines
    assert lines_before_quantity_change_count == lines_after.count()
    # stock allocation should be 2 now
    assert Stock.objects.first().quantity_allocated == 2
    line.refresh_from_db()
    # source line quantity should be decreased to 2
    assert line.quantity == 2
    # order should have the same delivery groups count
    assert order_with_items_and_stock.groups.count() == 1
    # a note in the order's history should be created
    assert OrderHistoryEntry.objects.get(
        order=order_with_items_and_stock).comment == (
            'Changed quantity for product %(product)s from'
            ' %(old_quantity)s to %(new_quantity)s') % {
                    'product': line.product,
                    'old_quantity': line_quantity_before_quantity_change,
                    'new_quantity': 2}


@pytest.mark.integration
@pytest.mark.django_db
def test_view_change_order_line_quantity_with_invalid_data(
        admin_client, order_with_items_and_stock):
    """
    user goes to order details page
    user selects the first order line with quantity 3 and try to change it to 0 and -1
    user gets an error.
    """
    lines = order_with_items_and_stock.get_items()
    line = lines.first()
    url = reverse(
        'dashboard:orderline-change-quantity', kwargs={
            'order_pk': order_with_items_and_stock.pk,
            'line_pk': line.pk})
    response = admin_client.post(
        url, {'quantity': 0})
    assert response.status_code == 400

def test_dashboard_change_quantity_form(request_cart_with_item, order):
    cart = request_cart_with_item
    group = DeliveryGroup.objects.create(order=order)
    add_items_to_delivery_group(group, cart.lines.all())
    order_line = group.items.get()
    variant = ProductVariant.objects.get(sku=order_line.product_sku)

    # Check max quantity validation
    form = ChangeQuantityForm(
        {'quantity': 9999},
        instance=order_line,
        variant=variant)
    assert not form.is_valid()
    assert form.errors['quantity'] == ['Ensure this value is less than or equal to 50.']

    # Check minimum quantity validation
    form = ChangeQuantityForm(
        {'quantity': 0},
        instance=order_line,
        variant=variant)
    assert not form.is_valid()
    assert group.items.get().stock.quantity_allocated == 1

    # Check available quantity validation
    form = ChangeQuantityForm(
        {'quantity': 20},
        instance=order_line,
        variant=variant)
    assert not form.is_valid()
    assert group.items.get().stock.quantity_allocated == 1
    assert form.errors['quantity'] == ['Only 4 remaining in stock.']

    # Save same quantity
    form = ChangeQuantityForm(
        {'quantity': 1},
        instance=order_line,
        variant=variant)
    assert form.is_valid()
    form.save()
    assert group.items.get().stock.quantity_allocated == 1
    # Increase quantity
    form = ChangeQuantityForm(
        {'quantity': 2},
        instance=order_line,
        variant = variant)
    assert form.is_valid()
    form.save()
    assert group.items.get().stock.quantity_allocated == 2
    # Decrease quantity
    form = ChangeQuantityForm(
        {'quantity': 1},
        instance=order_line,
        variant=variant)
    assert form.is_valid()
    form.save()
    assert group.items.get().stock.quantity_allocated == 1


@pytest.mark.integration
@pytest.mark.django_db
def test_view_split_order_line(admin_client, order_with_items_and_stock):
    """
    user goes to order details page
    user selects first order line with quantity 3 and moves 2 items
      to a new shipment
    user selects the line from the new shipment and moves all items
      back to the first shipment
    """
    lines_before_split = order_with_items_and_stock.get_items()
    lines_before_split_count = lines_before_split.count()
    line = lines_before_split.first()
    line_quantity_before_split = line.quantity
    quantity_allocated_before_split = line.stock.quantity_allocated
    old_delivery_group = DeliveryGroup.objects.get()

    url = reverse(
        'dashboard:orderline-split', kwargs={
            'order_pk': order_with_items_and_stock.pk,
            'line_pk': line.pk})
    response = admin_client.get(url)
    assert response.status_code == 200
    response = admin_client.post(
        url,
        {'quantity': 2, 'target_group': MoveItemsForm.NEW_SHIPMENT},
        follow=True)
    redirected_to, redirect_status_code = response.redirect_chain[-1]
    # check redirection
    assert redirect_status_code == 302
    assert get_url_path(redirected_to) == reverse(
        'dashboard:order-details',
        args=[order_with_items_and_stock.pk])
    # success messages should appear after redirect
    assert response.context['messages']
    lines_after = Order.objects.get().get_items()
    # order should have one more line
    assert lines_before_split_count + 1 == lines_after.count()
    # stock allocation should not be changed
    assert Stock.objects.first().quantity_allocated == quantity_allocated_before_split
    line.refresh_from_db()
    # source line quantity should be decreased to 1
    assert line.quantity == line_quantity_before_split - 2
    # order should have 2 delivery groups now
    assert order_with_items_and_stock.groups.count() == 2
    # a note in the order's history should be created
    new_group = DeliveryGroup.objects.last()
    assert OrderHistoryEntry.objects.get(
        order=order_with_items_and_stock).comment == (
                'Moved 2 items %(item)s from '
                '%(old_group)s to %(new_group)s') % {
                    'item': line,
                    'old_group': old_delivery_group,
                    'new_group': new_group}
    new_line = new_group.items.get()
    # the new line should contain the moved quantity
    assert new_line.quantity == 2
    url = reverse(
        'dashboard:orderline-split', kwargs={
            'order_pk': order_with_items_and_stock.pk,
            'line_pk': new_line.pk})
    admin_client.post(
        url, {'quantity': 2, 'target_group': old_delivery_group.pk})
    # an other note in the order's history should be created
    assert OrderHistoryEntry.objects.filter(
        order=order_with_items_and_stock).last().comment ==(
            'Moved 2 items %(item)s from removed '
            'group to %(new_group)s') % {
                'item': line,
                'new_group': old_delivery_group}
    # the new shipment should be removed
    assert order_with_items_and_stock.groups.count() == 1
    # the related order line should be removed
    assert lines_before_split_count == Order.objects.get().get_items().count()
    line.refresh_from_db()
    # the initial line should get the quantity restored to its initial value
    assert line_quantity_before_split == line.quantity


@pytest.mark.integration
@pytest.mark.django_db
@pytest.mark.parametrize('quantity', [0, 4])
def test_view_split_order_line_with_invalid_data(admin_client, order_with_items_and_stock, quantity):
    """
    user goes to order details page
    user selects first order line with quantity 3 and try move 0 and 4 items to a new shipment
    user gets an error and no delivery groups are created.
    """
    lines = order_with_items_and_stock.get_items()
    line = lines.first()
    url = reverse(
        'dashboard:orderline-split', kwargs={
            'order_pk': order_with_items_and_stock.pk,
            'line_pk': line.pk})
    response = admin_client.post(
        url, {'quantity': quantity, 'target_group': MoveItemsForm.NEW_SHIPMENT})
    assert response.status_code == 400
    assert DeliveryGroup.objects.count() == 1


@pytest.mark.integration
@pytest.mark.django_db
def test_view_order_invoice(
        admin_client, order_with_items_and_stock, billing_address):
    """
    user goes to order details page
    user clicks on Invoice button
    user downloads the invoice as PDF file
    """
    order_with_items_and_stock.shipping_address = billing_address
    order_with_items_and_stock.billing_address = billing_address
    order_with_items_and_stock.save()
    url = reverse(
        'dashboard:order-invoice', kwargs={
            'group_pk': order_with_items_and_stock.groups.all()[0].pk
        })
    response = admin_client.get(url)
    assert response.status_code == 200
    assert response['content-type'] == 'application/pdf'
    name = "invoice-%s-%s" % (order_with_items_and_stock.id,
                              order_with_items_and_stock.groups.all()[0].pk)
    assert response['Content-Disposition'] == 'filename=%s' % name


@pytest.mark.integration
@pytest.mark.django_db
def test_view_order_packing_slips(
        admin_client, order_with_items_and_stock, billing_address):
    """
    user goes to order details page
    user clicks on Packing Slips button
    user downloads the packing slips as PDF file
    """
    order_with_items_and_stock.shipping_address = billing_address
    order_with_items_and_stock.billing_address = billing_address
    order_with_items_and_stock.save()
    url = reverse(
        'dashboard:order-packing-slips', kwargs={
            'group_pk': order_with_items_and_stock.groups.all()[0].pk
        })
    response = admin_client.get(url)
    assert response.status_code == 200
    assert response['content-type'] == 'application/pdf'
    name = "packing-slip-%s-%s" % (
        order_with_items_and_stock.id,
        order_with_items_and_stock.groups.all()[0].pk)
    assert response['Content-Disposition'] == 'filename=%s' % name
