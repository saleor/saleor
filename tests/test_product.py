import datetime
import json
from unittest.mock import patch

from django.urls import reverse
from saleor.cart import CartStatus, utils
from saleor.cart.models import Cart
from saleor.product import ProductAvailabilityStatus, models
from saleor.product.models import Category, ProductImage
from saleor.product.thumbnails import create_product_thumbnails
from saleor.product.utils import (
    allocate_stock, deallocate_stock, decrease_stock, increase_stock)
from saleor.product.utils.availability import get_product_availability_status
from saleor.product.utils.variants_picker import get_variant_picker_data

from .utils import filter_products_by_attribute


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
        {'id': variant.pk, 'text': '123, Test product, $10.00'}]

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


@patch('saleor.product.thumbnails.create_thumbnails')
def test_create_product_thumbnails(
        mock_create_thumbnails, product_with_image):
    product_image = product_with_image.images.first()
    create_product_thumbnails(product_image.pk)
    assert mock_create_thumbnails.called_once_with(
        product_image.pk, ProductImage, 'products')
