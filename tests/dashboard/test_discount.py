from datetime import date
from decimal import Decimal

from django.urls import reverse
from prices import Money

from saleor.discount import DiscountValueType, VoucherType
from saleor.discount.models import Sale, Voucher


def test_sales_list(admin_client, sale):
    url = reverse('dashboard:sale-list')
    response = admin_client.get(url)
    assert response.status_code == 200


def test_vouchers_list(admin_client, voucher):
    url = reverse('dashboard:voucher-list')
    response = admin_client.get(url)
    assert response.status_code == 200


def test_voucher_shipping_add(admin_client):
    assert len(Voucher.objects.all()) == 0
    url = reverse('dashboard:voucher-add')
    data = {
        'code': 'TESTVOUCHER', 'name': 'Test Voucher',
        'start_date': '2018-01-01', 'end_date': '2018-06-01',
        'type': VoucherType.SHIPPING, 'discount_value': '15.99',
        'discount_value_type': DiscountValueType.FIXED,
        'shipping-limit': '59.99'}
    response = admin_client.post(url, data, follow=True)
    assert response.status_code == 200
    assert len(Voucher.objects.all()) == 1

    voucher = Voucher.objects.all()[0]
    assert voucher.type == VoucherType.SHIPPING
    assert voucher.code == data['code']
    assert voucher.name == data['name']
    assert voucher.start_date == date(2018, 1, 1)
    assert voucher.end_date == date(2018, 6, 1)
    assert voucher.discount_value_type == DiscountValueType.FIXED
    assert voucher.discount_value == Decimal('15.99')
    assert voucher.limit == Money('59.99', 'USD')


def test_view_sale_add(admin_client, default_category):
    url = reverse('dashboard:sale-add')
    data = {
        'name': 'Free products',
        'type': DiscountValueType.PERCENTAGE,
        'value': 100,
        'categories': [default_category.id]}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    assert Sale.objects.count() == 1
    sale = Sale.objects.first()
    assert sale.name == data['name']
    assert default_category in sale.categories.all()


def test_view_sale_add_requires_product_or_category(
        admin_client, default_category, product_in_stock):
    url = reverse('dashboard:sale-add')
    data = {
        'name': 'Free products',
        'type': DiscountValueType.PERCENTAGE,
        'value': 100}

    response = admin_client.post(url, data)

    assert response.status_code == 200
    assert Sale.objects.count() == 0

    data_with_category = data.copy()
    data_with_category.update({'categories': [default_category.id]})

    response = admin_client.post(url, data_with_category)

    assert response.status_code == 302
    assert Sale.objects.count() == 1

    data_with_product = data.copy()
    data_with_product.update({'products': [product_in_stock.id]})

    response = admin_client.post(url, data_with_product)

    assert response.status_code == 302
    assert Sale.objects.count() == 2
