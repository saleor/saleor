import datetime
import json
from unittest.mock import Mock

import pytest
from django.urls import reverse
from django.utils.encoding import smart_text
from tests.utils import filter_products_by_attribute

from saleor.cart import CartStatus, utils
from saleor.cart.models import Cart
from saleor.product import (
    ProductAvailabilityStatus, VariantAvailabilityStatus, models)
from saleor.product.models import Category
from saleor.product.utils import (
    allocate_stock, deallocate_stock, decrease_stock,
    get_attributes_display_map, get_availability,
    get_product_availability_status, get_variant_availability_status,
    get_variant_picker_data, increase_stock)


@pytest.fixture()
def product_with_no_attributes(product_type, default_category):
    product = models.Product.objects.create(
        name='Test product', price='10.00', product_type=product_type,
        category=default_category)
    return product


def test_stock_selector(product_in_stock):
    variant = product_in_stock.variants.get()
    preferred_stock = variant.select_stockrecord(5)
    assert preferred_stock.quantity_available >= 5


def test_allocate_stock(product_in_stock):
    variant = product_in_stock.variants.get()
    stock = variant.select_stockrecord(5)
    assert stock.quantity_allocated == 0
    allocate_stock(stock, 1)
    stock.refresh_from_db()
    assert stock.quantity_allocated == 1


def test_deallocate_stock(product_in_stock):
    stock = product_in_stock.variants.first().stock.first()
    stock.quantity = 100
    stock.quantity_allocated = 80
    stock.save()
    deallocate_stock(stock, 50)
    stock.refresh_from_db()
    assert stock.quantity == 100
    assert stock.quantity_allocated == 30


def test_decrease_stock(product_in_stock):
    stock = product_in_stock.variants.first().stock.first()
    stock.quantity = 100
    stock.quantity_allocated = 80
    stock.save()
    decrease_stock(stock, 50)
    stock.refresh_from_db()
    assert stock.quantity == 50
    assert stock.quantity_allocated == 30


def test_increase_stock(product_in_stock):
    stock = product_in_stock.variants.first().stock.first()
    stock.quantity = 100
    stock.quantity_allocated = 80
    stock.save()
    increase_stock(stock, 50)
    stock.refresh_from_db()
    assert stock.quantity == 150
    assert stock.quantity_allocated == 80


def test_product_page_redirects_to_correct_slug(client, product_in_stock):
    uri = product_in_stock.get_absolute_url()
    uri = uri.replace(product_in_stock.get_slug(), 'spanish-inquisition')
    response = client.get(uri)
    assert response.status_code == 301
    location = response['location']
    if location.startswith('http'):
        location = location.split('http://testserver')[1]
    assert location == product_in_stock.get_absolute_url()


def test_product_preview(admin_client, client, product_in_stock):
    product_in_stock.available_on = (
        datetime.date.today() + datetime.timedelta(days=7))
    product_in_stock.save()
    response = client.get(product_in_stock.get_absolute_url())
    assert response.status_code == 404
    response = admin_client.get(product_in_stock.get_absolute_url())
    assert response.status_code == 200


def test_availability(product_in_stock, monkeypatch, settings):
    availability = get_availability(product_in_stock)
    assert availability.price_range == product_in_stock.get_price_range()
    assert availability.price_range_local_currency is None
    monkeypatch.setattr(
        'django_prices_openexchangerates.models.get_rates',
        lambda c: {'PLN': Mock(rate=2)})
    settings.DEFAULT_COUNTRY = 'PL'
    settings.OPENEXCHANGERATES_API_KEY = 'fake-key'
    availability = get_availability(product_in_stock, local_currency='PLN')
    assert availability.price_range_local_currency.start.currency == 'PLN'
    assert availability.available


def test_available_products_only_published(product_list):
    available_products = models.Product.objects.available_products()
    assert available_products.count() == 2
    assert all([product.is_published for product in available_products])


def test_available_products_only_available(product_list):
    product = product_list[0]
    date_tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    product.available_on = date_tomorrow
    product.save()
    available_products = models.Product.objects.available_products()
    assert available_products.count() == 1
    assert all([product.is_available() for product in available_products])


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
    product_a.set_attribute(color_attribute.pk, color.pk)
    product_a.save()
    variant_b.set_attribute(color_attribute.pk, color.pk)
    variant_b.save()

    filtered = filter_products_by_attribute(models.Product.objects.all(),
                                            color_attribute.pk, color.pk)
    assert product_a in list(filtered)
    assert product_b in list(filtered)

    product_a.set_attribute(color_attribute.pk, color_2.pk)
    product_a.save()
    filtered = filter_products_by_attribute(models.Product.objects.all(),
                                            color_attribute.pk, color.pk)
    assert product_a not in list(filtered)
    assert product_b in list(filtered)
    filtered = filter_products_by_attribute(models.Product.objects.all(),
                                            color_attribute.pk, color_2.pk)
    assert product_a in list(filtered)
    assert product_b not in list(filtered)


def test_view_invalid_add_to_cart(client, product_in_stock, request_cart):
    variant = product_in_stock.variants.get()
    request_cart.add(variant, 2)
    response = client.post(
        reverse(
            'product:add-to-cart',
            kwargs={
                'slug': product_in_stock.get_slug(),
                'product_id': product_in_stock.pk}),
        {})
    assert response.status_code == 200
    assert request_cart.quantity == 2


def test_view_add_to_cart(client, product_in_stock, request_cart):
    variant = product_in_stock.variants.get()
    request_cart.add(variant, 1)
    response = client.post(
        reverse(
            'product:add-to-cart',
            kwargs={'slug': product_in_stock.get_slug(),
                    'product_id': product_in_stock.pk}),
        {'quantity': 1, 'variant': variant.pk})
    assert response.status_code == 302
    assert request_cart.quantity == 1


def test_adding_to_cart_with_current_user_token(
        admin_user, admin_client, product_in_stock):
    client = admin_client
    key = utils.COOKIE_NAME
    cart = Cart.objects.create(user=admin_user)
    variant = product_in_stock.variants.first()
    cart.add(variant, 1)

    response = client.get(reverse('cart:index'))
    utils.set_cart_cookie(cart, response)
    client.cookies[key] = response.cookies[key]

    client.post(
        reverse('product:add-to-cart',
                kwargs={'slug': product_in_stock.get_slug(),
                        'product_id': product_in_stock.pk}),
        {'quantity': 1, 'variant': variant.pk})

    assert Cart.objects.count() == 1
    assert Cart.objects.get(user=admin_user).pk == cart.pk


def test_adding_to_cart_with_another_user_token(
        admin_user, admin_client, product_in_stock, customer_user):
    client = admin_client
    key = utils.COOKIE_NAME
    cart = Cart.objects.create(user=customer_user)
    variant = product_in_stock.variants.first()
    cart.add(variant, 1)

    response = client.get(reverse('cart:index'))
    utils.set_cart_cookie(cart, response)
    client.cookies[key] = response.cookies[key]

    client.post(
        reverse('product:add-to-cart',
                kwargs={'slug': product_in_stock.get_slug(),
                        'product_id': product_in_stock.pk}),
        {'quantity': 1, 'variant': variant.pk})

    assert Cart.objects.count() == 2
    assert Cart.objects.get(user=admin_user).pk != cart.pk


def test_anonymous_adding_to_cart_with_another_user_token(
        client, product_in_stock, customer_user):
    key = utils.COOKIE_NAME
    cart = Cart.objects.create(user=customer_user)
    variant = product_in_stock.variants.first()
    cart.add(variant, 1)

    response = client.get(reverse('cart:index'))
    utils.set_cart_cookie(cart, response)
    client.cookies[key] = response.cookies[key]

    client.post(
        reverse('product:add-to-cart',
                kwargs={'slug': product_in_stock.get_slug(),
                        'product_id': product_in_stock.pk}),
        {'quantity': 1, 'variant': variant.pk})

    assert Cart.objects.count() == 2
    assert Cart.objects.get(user=None).pk != cart.pk


def test_adding_to_cart_with_deleted_cart_token(
        admin_user, admin_client, product_in_stock):
    client = admin_client
    key = utils.COOKIE_NAME
    cart = Cart.objects.create(user=admin_user)
    old_token = cart.token
    variant = product_in_stock.variants.first()
    cart.add(variant, 1)

    response = client.get(reverse('cart:index'))
    utils.set_cart_cookie(cart, response)
    client.cookies[key] = response.cookies[key]
    cart.delete()

    client.post(
        reverse('product:add-to-cart',
                kwargs={'slug': product_in_stock.get_slug(),
                        'product_id': product_in_stock.pk}),
        {'quantity': 1, 'variant': variant.pk})

    assert Cart.objects.count() == 1
    assert not Cart.objects.filter(token=old_token).exists()


def test_adding_to_cart_with_closed_cart_token(
        admin_user, admin_client, product_in_stock):
    client = admin_client
    key = utils.COOKIE_NAME
    cart = Cart.objects.create(user=admin_user)
    variant = product_in_stock.variants.first()
    cart.add(variant, 1)

    response = client.get(reverse('cart:index'))
    utils.set_cart_cookie(cart, response)
    client.cookies[key] = response.cookies[key]

    client.post(
        reverse('product:add-to-cart',
                kwargs={'slug': product_in_stock.get_slug(),
                        'product_id': product_in_stock.pk}),
        {'quantity': 1, 'variant': variant.pk})

    assert Cart.objects.filter(
        user=admin_user, status=CartStatus.OPEN).count() == 1


def test_get_attributes_display_map(product_in_stock):
    attributes = product_in_stock.product_type.product_attributes.all()
    attributes_display_map = get_attributes_display_map(
        product_in_stock, attributes)

    product_attr = product_in_stock.product_type.product_attributes.first()
    attr_value = product_attr.values.first()

    assert len(attributes_display_map) == 1
    assert attributes_display_map == {product_attr.pk: attr_value}


def test_get_attributes_display_map_empty(product_with_no_attributes):
    product = product_with_no_attributes
    attributes = product.product_type.product_attributes.all()

    assert get_attributes_display_map(product, attributes) == {}


def test_get_attributes_display_map_no_choices(product_in_stock):
    attributes = product_in_stock.product_type.product_attributes.all()
    product_attr = attributes.first()

    product_in_stock.set_attribute(product_attr.pk, -1)
    attributes_display_map = get_attributes_display_map(
        product_in_stock, attributes)

    assert attributes_display_map == {product_attr.pk: smart_text(-1)}


def test_product_availability_status(unavailable_product):
    product = unavailable_product
    product.product_type.has_variants = True

    # product is not published
    status = get_product_availability_status(product)
    assert status == ProductAvailabilityStatus.NOT_PUBLISHED

    product.is_published = True
    product.save()

    # product has no variants
    status = get_product_availability_status(product)
    assert status == ProductAvailabilityStatus.VARIANTS_MISSSING

    # product has variant but not stock records
    variant_1 = product.variants.create(sku='test-1')
    variant_2 = product.variants.create(sku='test-2')
    status = get_product_availability_status(product)
    assert status == ProductAvailabilityStatus.NOT_CARRIED

    # create empty stock records
    stock_1 = variant_1.stock.create(quantity=0)
    stock_2 = variant_2.stock.create(quantity=0)
    status = get_product_availability_status(product)
    assert status == ProductAvailabilityStatus.OUT_OF_STOCK

    # assign quantity to only one stock record
    stock_1.quantity = 5
    stock_1.save()
    status = get_product_availability_status(product)
    assert status == ProductAvailabilityStatus.LOW_STOCK

    # both stock records have some quantity
    stock_2.quantity = 5
    stock_2.save()
    status = get_product_availability_status(product)
    assert status == ProductAvailabilityStatus.READY_FOR_PURCHASE

    # set product availability date from future
    product.available_on = datetime.date.today() + datetime.timedelta(days=1)
    product.save()
    status = get_product_availability_status(product)
    assert status == ProductAvailabilityStatus.NOT_YET_AVAILABLE


def test_variant_availability_status(unavailable_product):
    product = unavailable_product
    product.product_type.has_variants = True

    variant = product.variants.create(sku='test')
    status = get_variant_availability_status(variant)
    assert status == VariantAvailabilityStatus.NOT_CARRIED

    stock = variant.stock.create(quantity=0)
    status = get_variant_availability_status(variant)
    assert status == VariantAvailabilityStatus.OUT_OF_STOCK

    stock.quantity = 5
    stock.save()
    status = get_variant_availability_status(variant)
    assert status == VariantAvailabilityStatus.AVAILABLE


def test_product_filter_before_filtering(
        authorized_client, product_in_stock, default_category):
    products = models.Product.objects.all().filter(
        category__name=default_category).order_by('-price')
    url = reverse(
        'product:category', kwargs={'path': default_category.slug,
                                    'category_id': default_category.pk})
    response = authorized_client.get(url)
    assert list(products) == list(response.context['filter_set'].qs)


def test_product_filter_product_exists(authorized_client, product_in_stock,
                                       default_category):
    products = (
        models.Product.objects.all()
        .filter(category__name=default_category)
        .order_by('-price'))
    url = reverse(
        'product:category', kwargs={
            'path': default_category.slug, 'category_id': default_category.pk})
    data = {'price_0': [''], 'price_1': ['20']}
    response = authorized_client.get(url, data)
    assert list(response.context['filter_set'].qs) == list(products)


def test_product_filter_product_does_not_exist(
        authorized_client, product_in_stock, default_category):
    url = reverse(
        'product:category', kwargs={
            'path': default_category.slug, 'category_id': default_category.pk})
    data = {'price_0': ['20'], 'price_1': ['']}
    response = authorized_client.get(url, data)
    assert not list(response.context['filter_set'].qs)


def test_product_filter_form(authorized_client, product_in_stock,
                             default_category):
    products = (
        models.Product.objects.all()
        .filter(category__name=default_category)
        .order_by('-price'))
    url = reverse(
        'product:category', kwargs={
            'path': default_category.slug, 'category_id': default_category.pk})
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
        'product:category', kwargs={
            'path': default_category.slug, 'category_id': default_category.pk})
    data = {'sort_by': '-price'}
    response = authorized_client.get(url, data)
    assert list(response.context['filter_set'].qs) == list(products)


def test_product_filter_sorted_by_wrong_parameter(
        authorized_client, product_in_stock, default_category):
    url = reverse(
        'product:category', kwargs={
            'path': default_category.slug, 'category_id': default_category.pk})
    data = {'sort_by': 'aaa'}
    response = authorized_client.get(url, data)
    assert not list(response.context['filter_set'].qs)


def test_get_variant_picker_data_proper_variant_count(product_in_stock):
    data = get_variant_picker_data(
        product_in_stock, discounts=None, local_currency=None)

    assert len(data['variantAttributes'][0]['values']) == 1


def test_view_ajax_available_variants_list(admin_client, product_in_stock):
    variant = product_in_stock.variants.first()
    variant_list = [
        {'id': variant.pk, 'text': '123, Test product (Size: Small), $10.00'}]

    url = reverse('dashboard:ajax-available-variants')
    response = admin_client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    resp_decoded = json.loads(response.content.decode('utf-8'))

    assert response.status_code == 200
    assert resp_decoded == {'results': variant_list}


def test_view_ajax_available_products_list(admin_client, product_in_stock):
    product_list = [{'id': product_in_stock.pk, 'text': 'Test product'}]

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
        default_category, product_in_stock, authorized_client):
    subcategory = Category.objects.create(
        name='sub', slug='test', parent=default_category)
    product = product_in_stock
    product.category = subcategory
    product.save()
    path = default_category.get_full_path()
    # URL to parent category view
    url = reverse(
        'product:category', kwargs={
            'path': path, 'category_id': default_category.pk})
    response = authorized_client.get(url)
    assert product in response.context_data['products'][0]
