import datetime
import io
import json
import os
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.core import serializers
from django.core.serializers.base import DeserializationError
from django.http import JsonResponse
from django.urls import reverse
from freezegun import freeze_time
from prices import Money, TaxedMoney, TaxedMoneyRange

from saleor.checkout import utils
from saleor.checkout.models import Checkout
from saleor.checkout.utils import add_variant_to_checkout
from saleor.dashboard.menu.utils import update_menu
from saleor.discount.models import Sale
from saleor.menu.models import MenuItemTranslation
from saleor.product import ProductAvailabilityStatus, models
from saleor.product.models import DigitalContentUrl
from saleor.product.thumbnails import create_product_thumbnails
from saleor.product.utils import (
    allocate_stock, deallocate_stock, decrease_stock, increase_stock)
from saleor.product.utils.attributes import get_product_attributes_data
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
    product.publication_date = (
        datetime.date.today() + datetime.timedelta(days=7))
    product.save()
    response = client.get(product.get_absolute_url())
    assert response.status_code == 404
    response = admin_client.get(product.get_absolute_url())
    assert response.status_code == 200


def test_filtering_by_attribute(db, color_attribute, category, settings):
    product_type_a = models.ProductType.objects.create(
        name='New class', has_variants=True)
    product_type_a.product_attributes.add(color_attribute)
    product_type_b = models.ProductType.objects.create(
        name='New class', has_variants=True)
    product_type_b.variant_attributes.add(color_attribute)
    product_a = models.Product.objects.create(
        name='Test product a', price=Money(10, settings.DEFAULT_CURRENCY),
        product_type=product_type_a, category=category)
    models.ProductVariant.objects.create(product=product_a, sku='1234')
    product_b = models.Product.objects.create(
        name='Test product b', price=Money(10, settings.DEFAULT_CURRENCY),
        product_type=product_type_b, category=category)
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


def test_render_home_page(client, product, site_settings, settings):
    # Tests if menu renders properly if none is assigned
    settings.LANGUAGE_CODE = 'fr'
    site_settings.top_menu = None
    site_settings.save()

    response = client.get(reverse('home'))
    assert response.status_code == 200


def test_render_home_page_with_translated_menu_items(
        client, product, menu_with_items, site_settings, settings):
    settings.LANGUAGE_CODE = 'fr'
    site_settings.top_menu = menu_with_items
    site_settings.save()

    for item in menu_with_items.items.all():
        MenuItemTranslation.objects.create(
            menu_item=item, language_code='fr',
            name='Translated name in French')
    update_menu(menu_with_items)

    response = client.get(reverse('home'))
    assert response.status_code == 200
    assert 'Translated name in French' in str(response.content)


def test_render_home_page_with_sale(client, product, sale):
    response = client.get(reverse('home'))
    assert response.status_code == 200


def test_render_home_page_with_taxes(client, product, vatlayer):
    response = client.get(reverse('home'))
    assert response.status_code == 200


def test_render_category(client, category, product):
    response = client.get(category.get_absolute_url())
    assert response.status_code == 200


def test_render_category_with_sale(client, category, product, sale):
    response = client.get(category.get_absolute_url())
    assert response.status_code == 200


def test_render_category_with_taxes(client, category, product, vatlayer):
    response = client.get(category.get_absolute_url())
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


def test_view_invalid_add_to_checkout(client, product, request_checkout):
    variant = product.variants.get()
    add_variant_to_checkout(request_checkout, variant, 2)
    response = client.post(
        reverse(
            'product:add-to-checkout',
            kwargs={
                'slug': product.get_slug(),
                'product_id': product.pk}),
        {})
    assert response.status_code == 200
    assert request_checkout.quantity == 2


def test_view_add_to_checkout(authorized_client, product, user_checkout):
    variant = product.variants.first()

    # Ignore stock
    variant.track_inventory = False
    variant.save()

    # Add the variant to the user checkout and retrieve the variant line
    add_variant_to_checkout(user_checkout, variant)
    checkout_line = user_checkout.lines.last()

    # Retrieve the test url
    checkout_url = reverse(
        'product:add-to-checkout',
        kwargs={'slug': product.get_slug(),
                'product_id': product.pk})

    # Attempt to set the quantity to 50
    response = authorized_client.post(
        checkout_url,
        {'quantity': 49, 'variant': variant.pk},
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')  # type: JsonResponse
    assert response.status_code == 200

    # Ensure the line quantity was updated to 50
    checkout_line.refresh_from_db(fields=['quantity'])
    assert checkout_line.quantity == 50

    # Attempt to increase the quantity to a too high count
    response = authorized_client.post(
        checkout_url,
        {'quantity': 1, 'variant': variant.pk},
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 400

    # Ensure the line quantity was not updated to 51
    checkout_line.refresh_from_db(fields=['quantity'])
    assert checkout_line.quantity == 50


def test_adding_to_checkout_with_current_user_token(
        customer_user, authorized_client, product, request_checkout_with_item):
    key = utils.COOKIE_NAME
    request_checkout_with_item.user = customer_user
    request_checkout_with_item.save()

    response = authorized_client.get(reverse('checkout:index'))

    utils.set_checkout_cookie(request_checkout_with_item, response)
    authorized_client.cookies[key] = response.cookies[key]
    variant = request_checkout_with_item.lines.first().variant
    url = reverse(
        'product:add-to-checkout',
        kwargs={'slug': product.get_slug(), 'product_id': product.pk})
    data = {'quantity': 1, 'variant': variant.pk}

    authorized_client.post(url, data)

    assert Checkout.objects.count() == 1
    assert Checkout.objects.get(
        user=customer_user).pk == request_checkout_with_item.pk


def test_adding_to_checkout_with_another_user_token(
        admin_user, admin_client, product, customer_user,
        request_checkout_with_item):
    client = admin_client
    key = utils.COOKIE_NAME
    request_checkout_with_item.user = customer_user
    request_checkout_with_item.save()

    response = client.get(reverse('checkout:index'))

    utils.set_checkout_cookie(request_checkout_with_item, response)
    client.cookies[key] = response.cookies[key]
    variant = request_checkout_with_item.lines.first().variant
    url = reverse(
        'product:add-to-checkout',
        kwargs={'slug': product.get_slug(), 'product_id': product.pk})
    data = {'quantity': 1, 'variant': variant.pk}

    client.post(url, data)

    assert Checkout.objects.count() == 2
    assert Checkout.objects.get(
        user=admin_user).pk != request_checkout_with_item.pk


def test_anonymous_adding_to_checkout_with_another_user_token(
        client, product, customer_user, request_checkout_with_item):
    key = utils.COOKIE_NAME
    request_checkout_with_item.user = customer_user
    request_checkout_with_item.save()

    response = client.get(reverse('checkout:index'))

    utils.set_checkout_cookie(request_checkout_with_item, response)
    client.cookies[key] = response.cookies[key]
    variant = product.variants.get()
    url = reverse(
        'product:add-to-checkout',
        kwargs={'slug': product.get_slug(), 'product_id': product.pk})
    data = {'quantity': 1, 'variant': variant.pk}

    client.post(url, data)

    assert Checkout.objects.count() == 2
    assert Checkout.objects.get(user=None).pk != request_checkout_with_item.pk


def test_adding_to_checkout_with_deleted_checkout_token(
        customer_user, authorized_client, product, request_checkout_with_item):
    key = utils.COOKIE_NAME
    request_checkout_with_item.user = customer_user
    request_checkout_with_item.save()
    old_token = request_checkout_with_item.token

    response = authorized_client.get(reverse('checkout:index'))

    utils.set_checkout_cookie(request_checkout_with_item, response)
    authorized_client.cookies[key] = response.cookies[key]
    request_checkout_with_item.delete()
    variant = product.variants.get()
    url = reverse(
        'product:add-to-checkout',
        kwargs={'slug': product.get_slug(), 'product_id': product.pk})
    data = {'quantity': 1, 'variant': variant.pk}

    authorized_client.post(url, data)

    assert Checkout.objects.count() == 1
    assert not Checkout.objects.filter(token=old_token).exists()


def test_adding_to_checkout_with_closed_checkout_token(
        customer_user, authorized_client, product, request_checkout_with_item):
    key = utils.COOKIE_NAME
    request_checkout_with_item.user = customer_user
    request_checkout_with_item.save()

    response = authorized_client.get(reverse('checkout:index'))
    utils.set_checkout_cookie(request_checkout_with_item, response)
    authorized_client.cookies[key] = response.cookies[key]
    variant = product.variants.get()
    url = reverse(
        'product:add-to-checkout',
        kwargs={'slug': product.get_slug(), 'product_id': product.pk})
    data = {'quantity': 1, 'variant': variant.pk}

    authorized_client.post(url, data)

    assert customer_user.checkouts.count() == 1


def test_product_filter_before_filtering(authorized_client, product, category):
    products = models.Product.objects.all().filter(
        category__name=category).order_by('-price')
    url = reverse(
        'product:category',
        kwargs={
            'slug': category.slug,
            'category_id': category.pk})

    response = authorized_client.get(url)

    assert list(products) == list(response.context['filter_set'].qs)


def test_product_filter_product_exists(authorized_client, product, category):
    products = (
        models.Product.objects.all()
        .filter(category__name=category)
        .order_by('-price'))
    url = reverse(
        'product:category',
        kwargs={
            'slug': category.slug,
            'category_id': category.pk})
    data = {'price_min': [''], 'price_max': ['20']}

    response = authorized_client.get(url, data)

    assert list(response.context['filter_set'].qs) == list(products)


def test_product_filter_product_does_not_exist(
        authorized_client, product, category):
    url = reverse(
        'product:category',
        kwargs={
            'slug': category.slug,
            'category_id': category.pk})
    data = {'price_min': ['20'], 'price_max': ['']}

    response = authorized_client.get(url, data)

    assert not list(response.context['filter_set'].qs)


def test_product_filter_form(authorized_client, product, category):
    products = (
        models.Product.objects.all()
        .filter(category__name=category)
        .order_by('-price'))
    url = reverse(
        'product:category',
        kwargs={
            'slug': category.slug,
            'category_id': category.pk})

    response = authorized_client.get(url)

    assert 'price' in response.context['filter_set'].form.fields.keys()
    assert 'sort_by' in response.context['filter_set'].form.fields.keys()
    assert list(response.context['filter_set'].qs) == list(products)


def test_product_filter_sorted_by_price_descending(
        authorized_client, product_list, category):
    products = (
        models.Product.objects.all()
        .filter(category__name=category, is_published=True)
        .order_by('-price'))
    url = reverse(
        'product:category',
        kwargs={
            'slug': category.slug,
            'category_id': category.pk})
    data = {'sort_by': '-price'}

    response = authorized_client.get(url, data)

    assert list(response.context['filter_set'].qs) == list(products)


def test_product_filter_sorted_by_wrong_parameter(
        authorized_client, product, category):
    url = reverse(
        'product:category',
        kwargs={
            'slug': category.slug,
            'category_id': category.pk})
    data = {'sort_by': 'aaa'}

    response = authorized_client.get(url, data)

    assert not response.context['filter_set'].form.is_valid()
    assert not response.context['products']


def test_get_variant_picker_data_proper_variant_count(product):
    data = get_variant_picker_data(
        product, discounts=None, taxes=None, local_currency=None)

    assert len(data['variantAttributes'][0]['values']) == 1


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
        category, product, authorized_client):
    subcategory = models.Category.objects.create(
        name='sub', slug='test', parent=category)
    product.category = subcategory
    product.save()
    # URL to parent category view
    url = reverse(
        'product:category', kwargs={
            'slug': category.slug, 'category_id': category.pk})
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
        product_type, category, taxes, sale, product_price,
        include_taxes_in_prices, include_taxes, include_discounts,
        product_net, product_gross, site_settings):
    site_settings.include_taxes_in_prices = include_taxes_in_prices
    site_settings.save()
    product = models.Product.objects.create(
        product_type=product_type,
        category=category,
        price=Money(product_price, 'USD'))
    variant = product.variants.create()

    price = variant.get_price(
        taxes=taxes if include_taxes else None,
        discounts=Sale.objects.all() if include_discounts else None)

    assert price == TaxedMoney(
        net=Money(product_net, 'USD'), gross=Money(product_gross, 'USD'))


def test_product_get_price_variant_has_no_price(
        product_type, category, taxes, site_settings):
    site_settings.include_taxes_in_prices = False
    site_settings.save()
    product = models.Product.objects.create(
        product_type=product_type,
        category=category,
        price=Money('10.00', 'USD'))
    variant = product.variants.create()

    price = variant.get_price(taxes=taxes)

    assert price == TaxedMoney(
        net=Money('10.00', 'USD'), gross=Money('12.30', 'USD'))


def test_product_get_price_variant_with_price(
        product_type, category, taxes, site_settings):
    site_settings.include_taxes_in_prices = False
    site_settings.save()
    product = models.Product.objects.create(
        product_type=product_type,
        category=category,
        price=Money('10.00', 'USD'))
    variant = product.variants.create(price_override=Money('20.00', 'USD'))

    price = variant.get_price(taxes=taxes)

    assert price == TaxedMoney(
        net=Money('20.00', 'USD'), gross=Money('24.60', 'USD'))


def test_product_get_price_range_with_variants(
        product_type, category, taxes, site_settings):
    site_settings.include_taxes_in_prices = False
    site_settings.save()
    product = models.Product.objects.create(
        product_type=product_type,
        category=category,
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
        product_type, category, taxes, site_settings):
    site_settings.include_taxes_in_prices = False
    site_settings.save()
    product = models.Product.objects.create(
        product_type=product_type,
        category=category,
        price=Money('10.00', 'USD'))

    price = product.get_price_range(taxes=taxes)

    expected_price = TaxedMoney(
        net=Money('10.00', 'USD'), gross=Money('12.30', 'USD'))
    assert price == TaxedMoneyRange(start=expected_price, stop=expected_price)


def test_product_get_price_do_not_charge_taxes(
        product_type, category, taxes, sale):
    product = models.Product.objects.create(
        product_type=product_type,
        category=category,
        price=Money('10.00', 'USD'),
        charge_taxes=False)
    variant = product.variants.create()

    price = variant.get_price(taxes=taxes, discounts=Sale.objects.all())

    assert price == TaxedMoney(
        net=Money('5.00', 'USD'), gross=Money('5.00', 'USD'))


def test_product_get_price_range_do_not_charge_taxes(
        product_type, category, taxes, sale):
    product = models.Product.objects.create(
        product_type=product_type,
        category=category,
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


def test_product_json_serialization(product):
    product.price = Money('10.00', 'USD')
    product.save()
    data = json.loads(serializers.serialize(
        "json", models.Product.objects.all()))
    assert data[0]['fields']['price'] == {
        '_type': 'Money', 'amount': '10.00', 'currency': 'USD'}


def test_product_json_deserialization(category, product_type):
    product_json = """
    [{{
        "model": "product.product",
        "pk": 60,
        "fields": {{
            "seo_title": null,
            "seo_description": "Future almost cup national.",
            "product_type": {product_type_pk},
            "name": "Kelly-Clark",
            "description": "Future almost cup national",
            "category": {category_pk},
            "price": {{"_type": "Money", "amount": "35.98", "currency": "USD"}},
            "publication_date": null,
            "is_published": true,
            "attributes": "{{\\"9\\": \\"24\\", \\"10\\": \\"26\\"}}",
            "updated_at": "2018-07-19T13:30:24.195Z",
            "is_featured": false,
            "charge_taxes": true,
            "tax_rate": "standard"
        }}
    }}]
    """.format(
        category_pk=category.pk, product_type_pk=product_type.pk)
    product_deserialized = list(serializers.deserialize(
        'json', product_json, ignorenonexistent=True))[0]
    product_deserialized.save()
    product = models.Product.objects.first()
    assert product.price == Money(Decimal('35.98'), 'USD')

    # same test for bytes
    product_json_bytes = bytes(product_json, 'utf-8')
    product_deserialized = list(serializers.deserialize(
        'json', product_json_bytes, ignorenonexistent=True))[0]
    product_deserialized.save()
    product = models.Product.objects.first()
    assert product.price == Money(Decimal('35.98'), 'USD')

    # same test for stream
    product_json_stream = io.StringIO(product_json)
    product_deserialized = list(serializers.deserialize(
        'json', product_json_stream, ignorenonexistent=True))[0]
    product_deserialized.save()
    product = models.Product.objects.first()
    assert product.price == Money(Decimal('35.98'), 'USD')


def test_json_no_currency_deserialization(category, product_type):
    product_json = """
    [{{
        "model": "product.product",
        "pk": 60,
        "fields": {{
            "seo_title": null,
            "seo_description": "Future almost cup national.",
            "product_type": {product_type_pk},
            "name": "Kelly-Clark",
            "description": "Future almost cup national",
            "category": {category_pk},
            "price": {{"_type": "Money", "amount": "35.98"}},
            "publication_date": null,
            "is_published": true,
            "attributes": "{{\\"9\\": \\"24\\", \\"10\\": \\"26\\"}}",
            "updated_at": "2018-07-19T13:30:24.195Z",
            "is_featured": false,
            "charge_taxes": true,
            "tax_rate": "standard"
        }}
    }}]
    """.format(
        category_pk=category.pk, product_type_pk=product_type.pk)
    with pytest.raises(DeserializationError):
        list(serializers.deserialize(
            'json', product_json, ignorenonexistent=True))


def test_variant_picker_data_with_translations(
        product, translated_variant_fr, settings):
    settings.LANGUAGE_CODE = 'fr'
    variant_picker_data = get_variant_picker_data(product)
    attribute = variant_picker_data['variantAttributes'][0]
    assert attribute['name'] == translated_variant_fr.name


def test_get_product_attributes_data_translation(
        product, settings, translated_attribute):
    settings.LANGUAGE_CODE = 'fr'
    attributes_data = get_product_attributes_data(product)
    attributes_keys = [attr.name for attr in attributes_data.keys()]
    assert translated_attribute.name in attributes_keys


def test_homepage_collection_render(
        client, site_settings, collection, product_list):
    collection.products.add(*product_list)
    site_settings.homepage_collection = collection
    site_settings.save()

    response = client.get(reverse('home'))
    assert response.status_code == 200
    products_in_context = {
        product[0] for product in response.context['products']}
    products_available = {
        product for product in product_list if product.is_published}
    assert products_in_context == products_available


def test_digital_product_view(client, digital_content):
    digital_content_url = DigitalContentUrl.objects.create(
        content=digital_content)
    url = digital_content_url.get_absolute_url()
    response = client.get(url)
    filename = os.path.basename(digital_content.content_file.name)

    assert response.status_code == 200
    assert response['content-type'] == 'image/jpeg'
    assert response['content-disposition'] == 'attachment; filename="%s"' % filename


def test_digital_product_view_url_downloaded_max_times(client, digital_content):
    digital_content.use_default_settings = False
    digital_content.max_downloads = 1
    digital_content.save()
    digital_content_url = DigitalContentUrl.objects.create(
        content=digital_content)

    url = digital_content_url.get_absolute_url()
    response = client.get(url)

    # first download
    assert response.status_code == 200

    # second download
    response = client.get(url)
    assert response.status_code == 404


def test_digital_product_view_url_expired(client, digital_content):
    digital_content.use_default_settings = False
    digital_content.url_valid_days = 10
    digital_content.save()

    with freeze_time('2018-05-31 12:00:01'):
        digital_content_url = DigitalContentUrl.objects.create(
            content=digital_content)

    url = digital_content_url.get_absolute_url()
    response = client.get(url)

    assert response.status_code == 404


def test_variant_picker_data_price_range(
        product_type, category, taxes, site_settings):

    site_settings.include_taxes_in_prices = False
    site_settings.save()

    product = models.Product.objects.create(
        product_type=product_type,
        category=category,
        price=Money('15.00', 'USD'))
    product.variants.create(sku='1')
    product.variants.create(sku='2', price_override=Money('20.00', 'USD'))
    product.variants.create(sku='3', price_override=Money('11.00', 'USD'))

    start = TaxedMoney(net=Money('11.00', 'USD'), gross=Money('13.53', 'USD'))
    stop = TaxedMoney(net=Money('20.00', 'USD'), gross=Money('24.60', 'USD'))

    picker_data = get_variant_picker_data(
        product, discounts=None, taxes=taxes, local_currency=None)

    min_price = picker_data['availability']['priceRange']['minPrice']
    min_price = TaxedMoney(
        net=Money(min_price['net'], min_price['currency']),
        gross=Money(min_price['gross'], min_price['currency']))

    max_price = picker_data['availability']['priceRange']['maxPrice']
    max_price = TaxedMoney(
        net=Money(max_price['net'], max_price['currency']),
        gross=Money(max_price['gross'], max_price['currency']))

    assert min_price == start
    assert max_price == stop
