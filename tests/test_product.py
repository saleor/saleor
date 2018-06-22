import datetime
import json
from unittest.mock import patch

import pytest
from django.urls import reverse
from prices import Money, TaxedMoney, TaxedMoneyRange

from saleor.checkout import utils
from saleor.checkout.models import Cart
from saleor.checkout.utils import add_variant_to_cart
from saleor.discount.models import Sale
from saleor.product import ProductAvailabilityStatus, models
from saleor.product.thumbnails import create_product_thumbnails
from saleor.product.utils import (
    allocate_stock, deallocate_stock, decrease_stock, increase_stock)
from saleor.product.utils.availability import get_product_availability_status
from saleor.product.utils.variants_picker import get_variant_picker_data

from .utils import filter_products_by_attribute


@pytest.mark.parametrize(
    'func, expected_quantity, expected_quantity_allocated',
    (
        (increase_stock, 150, 80),
        (decrease_stock, 50, 30),
        (deallocate_stock, 100, 30),
        (allocate_stock, 100, 130)))
def test_stock_utils(
        product, func, expected_quantity, expected_quantity_allocated):
    variant = product.variants.first()
    variant.quantity = 100
    variant.quantity_allocated = 80
    variant.save()
    func(variant, 50)
    variant.refresh_from_db()
    assert variant.quantity == expected_quantity
    assert variant.quantity_allocated == expected_quantity_allocated


def test_product_page_redirects_to_correct_slug(client, product):
    uri = product.get_absolute_url()
    uri = uri.replace(product.get_slug(), 'spanish-inquisition')
    response = client.get(uri)
    assert response.status_code == 301
    location = response['location']
    if location.startswith('http'):
        location = location.split('http://testserver')[1]
    assert location == product.get_absolute_url()


def test_product_preview(admin_client, client, product):
    product.available_on = (
        datetime.date.today() + datetime.timedelta(days=7))
    product.save()
    response = client.get(product.get_absolute_url())
    assert response.status_code == 404
    response = admin_client.get(product.get_absolute_url())
    assert response.status_code == 200


def test_filtering_by_attribute(db, color_attribute, default_category):
    product_type_a = models.ProductType.objects.create(
        name='New class', has_variants=True)
    product_type_a.product_attributes.add(color_attribute)
    product_type_b = models.ProductType.objects.create(
        name='New class', has_variants=True)
    product_type_b.variant_attributes.add(color_attribute)
    product_a = models.Product.objects.create(
        name='Test product a', price=10, product_type=product_type_a,
        category=default_category)
    models.ProductVariant.objects.create(product=product_a, sku='1234')
    product_b = models.Product.objects.create(
        name='Test product b', price=10, product_type=product_type_b,
        category=default_category)
    variant_b = models.ProductVariant.objects.create(product=product_b,
                                                     sku='12345')
    color = color_attribute.values.first()
    color_2 = color_attribute.values.last()
    product_a.attributes[str(color_attribute.pk)] = str(color.pk)
    product_a.save()
    variant_b.attributes[str(color_attribute.pk)] = str(color.pk)
    variant_b.save()

    filtered = filter_products_by_attribute(models.Product.objects.all(),
                                            color_attribute.pk, color.pk)
    assert product_a in list(filtered)
    assert product_b in list(filtered)

    product_a.attributes[str(color_attribute.pk)] = str(color_2.pk)
    product_a.save()
    filtered = filter_products_by_attribute(models.Product.objects.all(),
                                            color_attribute.pk, color.pk)
    assert product_a not in list(filtered)
    assert product_b in list(filtered)
    filtered = filter_products_by_attribute(models.Product.objects.all(),
                                            color_attribute.pk, color_2.pk)
    assert product_a in list(filtered)
    assert product_b not in list(filtered)


def test_render_home_page(client, product):
    response = client.get(reverse('home'))
    assert response.status_code == 200


def test_render_home_page_with_sale(client, product, sale):
    response = client.get(reverse('home'))
    assert response.status_code == 200


def test_render_home_page_with_taxes(client, product, vatlayer):
    response = client.get(reverse('home'))
    assert response.status_code == 200


def test_render_category(client, default_category, product):
    response = client.get(default_category.get_absolute_url())
    assert response.status_code == 200


def test_render_category_with_sale(client, default_category, product, sale):
    response = client.get(default_category.get_absolute_url())
    assert response.status_code == 200


def test_render_category_with_taxes(
        client, default_category, product, vatlayer):
    response = client.get(default_category.get_absolute_url())
    assert response.status_code == 200


def test_render_product_detail(client, product):
    response = client.get(product.get_absolute_url())
    assert response.status_code == 200


def test_render_product_detail_with_sale(client, product, sale):
    response = client.get(product.get_absolute_url())
    assert response.status_code == 200


def test_render_product_detail_with_taxes(client, product, vatlayer):
    response = client.get(product.get_absolute_url())
    assert response.status_code == 200


def test_view_invalid_add_to_cart(client, product, request_cart):
    variant = product.variants.get()
    add_variant_to_cart(request_cart, variant, 2)
    response = client.post(
        reverse(
            'product:add-to-cart',
            kwargs={
                'slug': product.get_slug(),
                'product_id': product.pk}),
        {})
    assert response.status_code == 200
    assert request_cart.quantity == 2


def test_view_add_to_cart(client, product, request_cart_with_item):
    variant = request_cart_with_item.lines.get().variant
    response = client.post(
        reverse(
            'product:add-to-cart',
            kwargs={'slug': product.get_slug(),
                    'product_id': product.pk}),
        {'quantity': 1, 'variant': variant.pk})
    assert response.status_code == 302
    assert request_cart_with_item.quantity == 1


def test_adding_to_cart_with_current_user_token(
        customer_user, authorized_client, product, request_cart_with_item):
    key = utils.COOKIE_NAME
    request_cart_with_item.user = customer_user
    request_cart_with_item.save()

    response = authorized_client.get(reverse('cart:index'))

    utils.set_cart_cookie(request_cart_with_item, response)
    authorized_client.cookies[key] = response.cookies[key]
    variant = request_cart_with_item.lines.first().variant
    url = reverse(
        'product:add-to-cart',
        kwargs={'slug': product.get_slug(), 'product_id': product.pk})
    data = {'quantity': 1, 'variant': variant.pk}

    authorized_client.post(url, data)

    assert Cart.objects.count() == 1
    assert Cart.objects.get(user=customer_user).pk == request_cart_with_item.pk


def test_adding_to_cart_with_another_user_token(
        admin_user, admin_client, product, customer_user, request_cart_with_item):
    client = admin_client
    key = utils.COOKIE_NAME
    request_cart_with_item.user = customer_user
    request_cart_with_item.save()

    response = client.get(reverse('cart:index'))

    utils.set_cart_cookie(request_cart_with_item, response)
    client.cookies[key] = response.cookies[key]
    variant = request_cart_with_item.lines.first().variant
    url = reverse(
        'product:add-to-cart',
        kwargs={'slug': product.get_slug(), 'product_id': product.pk})
    data = {'quantity': 1, 'variant': variant.pk}

    client.post(url, data)

    assert Cart.objects.count() == 2
    assert Cart.objects.get(user=admin_user).pk != request_cart_with_item.pk


def test_anonymous_adding_to_cart_with_another_user_token(
        client, product, customer_user, request_cart_with_item):
    key = utils.COOKIE_NAME
    request_cart_with_item.user = customer_user
    request_cart_with_item.save()

    response = client.get(reverse('cart:index'))

    utils.set_cart_cookie(request_cart_with_item, response)
    client.cookies[key] = response.cookies[key]
    variant = product.variants.get()
    url = reverse(
        'product:add-to-cart',
        kwargs={'slug': product.get_slug(), 'product_id': product.pk})
    data = {'quantity': 1, 'variant': variant.pk}

    client.post(url, data)

    assert Cart.objects.count() == 2
    assert Cart.objects.get(user=None).pk != request_cart_with_item.pk


def test_adding_to_cart_with_deleted_cart_token(
        customer_user, authorized_client, product, request_cart_with_item):
    key = utils.COOKIE_NAME
    request_cart_with_item.user = customer_user
    request_cart_with_item.save()
    old_token = request_cart_with_item.token

    response = authorized_client.get(reverse('cart:index'))

    utils.set_cart_cookie(request_cart_with_item, response)
    authorized_client.cookies[key] = response.cookies[key]
    request_cart_with_item.delete()
    variant = product.variants.get()
    url = reverse(
        'product:add-to-cart',
        kwargs={'slug': product.get_slug(), 'product_id': product.pk})
    data = {'quantity': 1, 'variant': variant.pk}

    authorized_client.post(url, data)

    assert Cart.objects.count() == 1
    assert not Cart.objects.filter(token=old_token).exists()


def test_adding_to_cart_with_closed_cart_token(
        customer_user, authorized_client, product, request_cart_with_item):
    key = utils.COOKIE_NAME
    request_cart_with_item.user = customer_user
    request_cart_with_item.save()

    response = authorized_client.get(reverse('cart:index'))
    utils.set_cart_cookie(request_cart_with_item, response)
    authorized_client.cookies[key] = response.cookies[key]
    variant = product.variants.get()
    url = reverse(
        'product:add-to-cart',
        kwargs={'slug': product.get_slug(), 'product_id': product.pk})
    data = {'quantity': 1, 'variant': variant.pk}

    authorized_client.post(url, data)

    assert customer_user.carts.count() == 1


def test_product_filter_before_filtering(
        authorized_client, product, default_category):
    products = models.Product.objects.all().filter(
        category__name=default_category).order_by('-price')
    url = reverse(
        'product:category',
        kwargs={
            'path': default_category.slug,
            'category_id': default_category.pk})

    response = authorized_client.get(url)

    assert list(products) == list(response.context['filter_set'].qs)


def test_product_filter_product_exists(authorized_client, product,
                                       default_category):
    products = (
        models.Product.objects.all()
        .filter(category__name=default_category)
        .order_by('-price'))
    url = reverse(
        'product:category',
        kwargs={
            'path': default_category.slug,
            'category_id': default_category.pk})
    data = {'price_0': [''], 'price_1': ['20']}

    response = authorized_client.get(url, data)

    assert list(response.context['filter_set'].qs) == list(products)


def test_product_filter_product_does_not_exist(
        authorized_client, product, default_category):
    url = reverse(
        'product:category',
        kwargs={
            'path': default_category.slug,
            'category_id': default_category.pk})
    data = {'price_0': ['20'], 'price_1': ['']}

    response = authorized_client.get(url, data)

    assert not list(response.context['filter_set'].qs)


def test_product_filter_form(authorized_client, product,
                             default_category):
    products = (
        models.Product.objects.all()
        .filter(category__name=default_category)
        .order_by('-price'))
    url = reverse(
        'product:category',
        kwargs={
            'path': default_category.slug,
            'category_id': default_category.pk})

    response = authorized_client.get(url)

    assert 'price' in response.context['filter_set'].form.fields.keys()
    assert 'sort_by' in response.context['filter_set'].form.fields.keys()
    assert list(response.context['filter_set'].qs) == list(products)


def test_product_filter_sorted_by_price_descending(
        authorized_client, product_list, default_category):
    products = (
        models.Product.objects.all()
        .filter(category__name=default_category, is_published=True)
        .order_by('-price'))
    url = reverse(
        'product:category',
        kwargs={
            'path': default_category.slug,
            'category_id': default_category.pk})
    data = {'sort_by': '-price'}

    response = authorized_client.get(url, data)

    assert list(response.context['filter_set'].qs) == list(products)


def test_product_filter_sorted_by_wrong_parameter(
        authorized_client, product, default_category):
    url = reverse(
        'product:category',
        kwargs={
            'path': default_category.slug,
            'category_id': default_category.pk})
    data = {'sort_by': 'aaa'}

    response = authorized_client.get(url, data)

    assert not list(response.context['filter_set'].qs)


def test_get_variant_picker_data_proper_variant_count(product):
    data = get_variant_picker_data(
        product, discounts=None, taxes=None, local_currency=None)

    assert len(data['variantAttributes'][0]['values']) == 1


def test_view_ajax_available_variants_list(admin_client, product):
    variant = product.variants.first()
    variant_list = [
        {'id': variant.pk, 'text': '123, Test product (123), $10.00'}]
    url = reverse('dashboard:ajax-available-variants')

    response = admin_client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    resp_decoded = json.loads(response.content.decode('utf-8'))
    assert response.status_code == 200
    assert resp_decoded == {'results': variant_list}


def test_view_ajax_available_products_list(admin_client, product):
    product_list = [{'id': product.pk, 'text': 'Test product'}]
    url = reverse('dashboard:ajax-products')

    response = admin_client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    resp_decoded = json.loads(response.content.decode('utf-8'))
    assert response.status_code == 200
    assert resp_decoded == {'results': product_list}


def test_render_product_page_with_no_variant(
        unavailable_product, admin_client):
    product = unavailable_product
    product.is_published = True
    product.product_type.has_variants = True
    product.save()
    status = get_product_availability_status(product)
    assert status == ProductAvailabilityStatus.VARIANTS_MISSSING
    url = reverse(
        'product:details',
        kwargs={'product_id': product.pk, 'slug': product.get_slug()})
    response = admin_client.get(url)
    assert response.status_code == 200


def test_include_products_from_subcategories_in_main_view(
        default_category, product, authorized_client):
    subcategory = models.Category.objects.create(
        name='sub', slug='test', parent=default_category)
    product.category = subcategory
    product.save()
    path = default_category.get_full_path()
    # URL to parent category view
    url = reverse(
        'product:category', kwargs={
            'path': path, 'category_id': default_category.pk})
    response = authorized_client.get(url)
    assert product in response.context_data['products'][0]


@patch('saleor.product.thumbnails.create_thumbnails')
def test_create_product_thumbnails(
        mock_create_thumbnails, product_with_image):
    product_image = product_with_image.images.first()
    create_product_thumbnails(product_image.pk)
    assert mock_create_thumbnails.called_once_with(
        product_image.pk, models.ProductImage, 'products')


@pytest.mark.parametrize(
    'product_price, include_taxes_in_prices, include_taxes, include_discounts,'
    'product_net, product_gross', [
        ('10.00', False, False, False, '10.00', '10.00'),
        ('10.00', False, True, False, '10.00', '12.30'),
        ('15.00', False, False, True, '10.00', '10.00'),
        ('15.00', False, True, True, '10.00', '12.30'),
        ('10.00', True, False, False, '10.00', '10.00'),
        ('10.00', True, True, False, '8.13', '10.00'),
        ('15.00', True, False, True, '10.00', '10.00'),
        ('15.00', True, True, True, '8.13', '10.00')])
def test_get_price(
        product_type, default_category, taxes, sale, product_price,
        include_taxes_in_prices, include_taxes, include_discounts,
        product_net, product_gross, site_settings):
    site_settings.include_taxes_in_prices = include_taxes_in_prices
    site_settings.save()
    product = models.Product.objects.create(
        product_type=product_type,
        category=default_category,
        price=Money(product_price, 'USD'))
    variant = product.variants.create()

    price = variant.get_price(
        taxes=taxes if include_taxes else None,
        discounts=Sale.objects.all() if include_discounts else None)

    assert price == TaxedMoney(
        net=Money(product_net, 'USD'), gross=Money(product_gross, 'USD'))


def test_product_get_price_variant_has_no_price(
        product_type, default_category, taxes, site_settings):
    site_settings.include_taxes_in_prices = False
    site_settings.save()
    product = models.Product.objects.create(
        product_type=product_type,
        category=default_category,
        price=Money('10.00', 'USD'))
    variant = product.variants.create()

    price = variant.get_price(taxes=taxes)

    assert price == TaxedMoney(
        net=Money('10.00', 'USD'), gross=Money('12.30', 'USD'))


def test_product_get_price_variant_with_price(
        product_type, default_category, taxes, site_settings):
    site_settings.include_taxes_in_prices = False
    site_settings.save()
    product = models.Product.objects.create(
        product_type=product_type,
        category=default_category,
        price=Money('10.00', 'USD'))
    variant = product.variants.create(price_override=Money('20.00', 'USD'))

    price = variant.get_price(taxes=taxes)

    assert price == TaxedMoney(
        net=Money('20.00', 'USD'), gross=Money('24.60', 'USD'))


def test_product_get_price_range_with_variants(
        product_type, default_category, taxes, site_settings):
    site_settings.include_taxes_in_prices = False
    site_settings.save()
    product = models.Product.objects.create(
        product_type=product_type,
        category=default_category,
        price=Money('15.00', 'USD'))
    product.variants.create(sku='1')
    product.variants.create(sku='2', price_override=Money('20.00', 'USD'))
    product.variants.create(sku='3', price_override=Money('11.00', 'USD'))

    price = product.get_price_range(taxes=taxes)

    start = TaxedMoney(
        net=Money('11.00', 'USD'), gross=Money('13.53', 'USD'))
    stop = TaxedMoney(
        net=Money('20.00', 'USD'), gross=Money('24.60', 'USD'))
    assert price == TaxedMoneyRange(start=start, stop=stop)


def test_product_get_price_range_no_variants(
        product_type, default_category, taxes, site_settings):
    site_settings.include_taxes_in_prices = False
    site_settings.save()
    product = models.Product.objects.create(
        product_type=product_type,
        category=default_category,
        price=Money('10.00', 'USD'))

    price = product.get_price_range(taxes=taxes)

    expected_price = TaxedMoney(
        net=Money('10.00', 'USD'), gross=Money('12.30', 'USD'))
    assert price == TaxedMoneyRange(start=expected_price, stop=expected_price)


def test_product_get_price_do_not_charge_taxes(
        product_type, default_category, taxes, sale):
    product = models.Product.objects.create(
        product_type=product_type,
        category=default_category,
        price=Money('10.00', 'USD'),
        charge_taxes=False)
    variant = product.variants.create()

    price = variant.get_price(taxes=taxes, discounts=Sale.objects.all())

    assert price == TaxedMoney(
        net=Money('5.00', 'USD'), gross=Money('5.00', 'USD'))


def test_product_get_price_range_do_not_charge_taxes(
        product_type, default_category, taxes, sale):
    product = models.Product.objects.create(
        product_type=product_type,
        category=default_category,
        price=Money('10.00', 'USD'),
        charge_taxes=False)

    price = product.get_price_range(taxes=taxes, discounts=Sale.objects.all())

    expected_price = TaxedMoney(
        net=Money('5.00', 'USD'), gross=Money('5.00', 'USD'))
    assert price == TaxedMoneyRange(start=expected_price, stop=expected_price)


def test_variant_base_price(product):
    variant = product.variants.get()
    assert variant.base_price == product.price

    variant.price_override = Money('15.00', 'USD')
    variant.save()

    assert variant.base_price == variant.price_override
