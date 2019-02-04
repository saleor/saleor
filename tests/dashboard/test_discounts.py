import json
from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest
from django.urls import reverse
from prices import Money, TaxedMoney

from saleor.dashboard.order.utils import get_voucher_discount_for_order
from saleor.discount import DiscountValueType, VoucherType
from saleor.discount.models import NotApplicable, Sale, Voucher
from saleor.product.models import Collection


def test_sales_list(admin_client, sale):
    url = reverse('dashboard:sale-list')
    response = admin_client.get(url)
    assert response.status_code == 200


def test_vouchers_list(admin_client, voucher):
    url = reverse('dashboard:voucher-list')
    response = admin_client.get(url)
    assert response.status_code == 200


def test_voucher_shipping_add(admin_client):
    assert Voucher.objects.count() == 0
    url = reverse('dashboard:voucher-add')
    data = {
        'code': 'TESTVOUCHER', 'name': 'Test Voucher',
        'start_date': '2018-01-01', 'end_date': '2018-06-01',
        'type': VoucherType.SHIPPING, 'discount_value': '15.99',
        'discount_value_type': DiscountValueType.FIXED,
        'shipping-min_amount_spent': '59.99'}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert Voucher.objects.count() == 1

    voucher = Voucher.objects.all()[0]
    assert voucher.type == VoucherType.SHIPPING
    assert voucher.code == data['code']
    assert voucher.name == data['name']
    assert voucher.start_date == date(2018, 1, 1)
    assert voucher.end_date == date(2018, 6, 1)
    assert voucher.discount_value_type == DiscountValueType.FIXED
    assert voucher.discount_value == Decimal('15.99')
    assert voucher.min_amount_spent == Money('59.99', 'USD')


def test_view_sale_add(admin_client, category, collection):
    url = reverse('dashboard:sale-add')
    data = {
        'name': 'Free products',
        'type': DiscountValueType.PERCENTAGE,
        'value': 100,
        'categories': [category.id],
        'collections': [collection.id],
        'start_date': '2018-01-01'}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    assert Sale.objects.count() == 1
    sale = Sale.objects.first()
    assert sale.name == data['name']
    assert category in sale.categories.all()
    assert collection in sale.collections.all()


def test_view_sale_add_requires_product_category_or_collection(
        admin_client, category, product, collection):
    initial_sales_count = Sale.objects.count()
    url = reverse('dashboard:sale-add')
    data = {
        'name': 'Free products',
        'type': DiscountValueType.PERCENTAGE,
        'value': 100,
        'start_date': '2018-01-01'}

    response = admin_client.post(url, data)

    assert response.status_code == 200
    assert Sale.objects.count() == initial_sales_count
    products_data = [
        {'categories': [category.id]},
        {'products': [product.id]}, {'collections': [collection.pk]}]
    for count, proper_data in enumerate(products_data):
        proper_data.update(data)
        response = admin_client.post(url, proper_data)
        assert response.status_code == 302
        assert Sale.objects.count() == 1 + initial_sales_count + count


@pytest.mark.parametrize(
    'total, discount_value, discount_type, min_amount_spent, expected_value', [
        ('100', 10, DiscountValueType.FIXED, None, 10),
        ('100.05', 10, DiscountValueType.PERCENTAGE, 100, 10)])
def test_value_voucher_order_discount(
        settings, total, discount_value, discount_type, min_amount_spent, expected_value):
    voucher = Voucher(
        code='unique', type=VoucherType.VALUE,
        discount_value_type=discount_type,
        discount_value=discount_value,
        min_amount_spent=Money(min_amount_spent, 'USD') if min_amount_spent is not None else None)
    subtotal = TaxedMoney(net=Money(total, 'USD'), gross=Money(total, 'USD'))
    order = Mock(get_subtotal=Mock(return_value=subtotal), voucher=voucher)
    discount = get_voucher_discount_for_order(order)
    assert discount == Money(expected_value, 'USD')


@pytest.mark.parametrize(
    'shipping_cost, discount_value, discount_type, expected_value', [
        (10, 50, DiscountValueType.PERCENTAGE, 5),
        (10, 20, DiscountValueType.FIXED, 10)])
def test_shipping_voucher_order_discount(
        shipping_cost, discount_value, discount_type, expected_value):
    voucher = Voucher(
        code='unique', type=VoucherType.SHIPPING,
        discount_value_type=discount_type,
        discount_value=discount_value,
        min_amount_spent=None)
    subtotal = TaxedMoney(net=Money(100, 'USD'), gross=Money(100, 'USD'))
    shipping_total = TaxedMoney(
        net=Money(shipping_cost, 'USD'), gross=Money(shipping_cost, 'USD'))
    order = Mock(
        get_subtotal=Mock(return_value=subtotal),
        shipping_price=shipping_total,
        voucher=voucher)
    discount = get_voucher_discount_for_order(order)
    assert discount == Money(expected_value, 'USD')


def test_shipping_voucher_checkout_discount_not_applicable_returns_zero():
    voucher = Voucher(
        code='unique', type=VoucherType.SHIPPING,
        discount_value_type=DiscountValueType.FIXED,
        discount_value=10,
        min_amount_spent=Money(20, 'USD'))
    price = TaxedMoney(net=Money(10, 'USD'), gross=Money(10, 'USD'))
    order = Mock(
        get_subtotal=Mock(return_value=price),
        shipping_price=price,
        voucher=voucher)
    with pytest.raises(NotApplicable):
        get_voucher_discount_for_order(order)


def test_product_voucher_checkout_discount_raises_not_applicable(
        order_with_lines, product_with_images):
    discounted_product = product_with_images
    voucher = Voucher(
        code='unique', type=VoucherType.PRODUCT,
        discount_value_type=DiscountValueType.FIXED,
        discount_value=10)
    voucher.save()
    voucher.products.add(discounted_product)
    order_with_lines.voucher = voucher
    order_with_lines.save()
    # Offer is valid only for products listed in voucher
    with pytest.raises(NotApplicable):
        get_voucher_discount_for_order(order_with_lines)


def test_category_voucher_checkout_discount_raises_not_applicable(
        order_with_lines):
    discounted_collection = Collection.objects.create(
        name='Discounted', slug='discou')
    voucher = Voucher(
        code='unique', type=VoucherType.COLLECTION,
        discount_value_type=DiscountValueType.FIXED,
        discount_value=10)
    voucher.save()
    voucher.collections.add(discounted_collection)
    order_with_lines.voucher = voucher
    order_with_lines.save()
    # Discount should be valid only for items in the discounted collections
    with pytest.raises(NotApplicable):
        get_voucher_discount_for_order(order_with_lines)


def test_ajax_voucher_list(admin_client, voucher):
    voucher.name = 'Summer sale'
    voucher.save()
    vouchers_list = [{'id': voucher.pk, 'text': str(voucher)}]
    url = reverse('dashboard:ajax-vouchers')

    response = admin_client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    resp_decoded = json.loads(response.content.decode('utf-8'))

    assert response.status_code == 200
    assert resp_decoded == {'results': vouchers_list}
