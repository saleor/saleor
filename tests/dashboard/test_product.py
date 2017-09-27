# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import pytest
from django import forms
from django.core.urlresolvers import reverse
from django.utils.encoding import smart_text
from mock import Mock

from saleor.dashboard.product.forms import (
    ProductClassForm, ProductClassSelectorForm, ProductForm)
from saleor.product.models import (
    Product, ProductAttribute, ProductClass, ProductImage, ProductVariant,
    Stock, StockLocation)


HTTP_STATUS_OK = 200
HTTP_REDIRECTION = 302


@pytest.mark.integration
@pytest.mark.django_db
def test_stock_record_update_works(admin_client, product_in_stock):
    variant = product_in_stock.variants.get()
    stock = variant.stock.order_by('-quantity_allocated').first()
    quantity = stock.quantity
    quantity_allocated = stock.quantity_allocated
    url = reverse(
        'dashboard:variant-stock-update', kwargs={
            'product_pk': product_in_stock.pk,
            'variant_pk': variant.pk,
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


def test_edit_used_product_class(db):
    product_class = ProductClass.objects.create(name='New class',
                                                has_variants=True)
    product = Product.objects.create(
        name='Test product', price=10, product_class=product_class)
    ProductVariant.objects.create(product=product, sku='1234')

    # When all products have only one variant you can change
    # has_variants to false
    assert product.variants.all().count() == 1
    data = {'name': product_class.name,
            'product_attributes': product_class.product_attributes.all(),
            'variant_attributes': product_class.variant_attributes.all(),
            'has_variants': False}
    form = ProductClassForm(data, instance=product_class)
    assert form.is_valid()

    data = {'name': product_class.name,
            'product_attributes': product_class.product_attributes.all(),
            'variant_attributes': product_class.variant_attributes.all(),
            'has_variants': True}
    form = ProductClassForm(data, instance=product_class)
    assert form.is_valid()

    # Test has_variants validator which prevents turning off when product
    # has multiple variants
    ProductVariant.objects.create(product=product, sku='12345')
    assert product.variants.all().count() == 2
    data = {'name': product_class.name,
            'product_attributes': product_class.product_attributes.all(),
            'variant_attributes': product_class.variant_attributes.all(),
            'has_variants': False}
    form = ProductClassForm(data, instance=product_class)
    assert not form.is_valid()
    assert 'has_variants' in form.errors.keys()


def test_change_attributes_in_product_form(db, product_in_stock,
                                           color_attribute):
    product = product_in_stock
    product_class = product.product_class
    text_attribute = ProductAttribute.objects.create(slug='author',
                                                     name='Author')
    product_class.product_attributes.add(text_attribute)
    color_value = color_attribute.values.first()
    new_author = 'Main Tester'
    new_color = color_value.pk
    data = {'name': product.name,
            'price': product.price.gross,
            'categories': [c.pk for c in product.categories.all()],
            'description': 'description',
            'attribute-author': new_author,
            'attribute-color': new_color}
    form = ProductForm(data, instance=product)
    assert form.is_valid()
    product = form.save()
    assert product.get_attribute(color_attribute.pk) == smart_text(new_color)
    assert product.get_attribute(text_attribute.pk) == new_author


def test_get_formfield_name_with_unicode_characters(db):
    text_attribute = ProductAttribute.objects.create(slug=u'ąęαβδηθλμπ',
                                                     name=u'ąęαβδηθλμπ')
    assert text_attribute.get_formfield_name() == 'attribute-ąęαβδηθλμπ'


def test_view_product_toggle_publish(db, admin_client, product_in_stock):
    product = product_in_stock
    url = reverse('dashboard:product-publish', kwargs={'pk': product.pk})
    response = admin_client.post(url)
    assert response.status_code == HTTP_STATUS_OK
    data = {'success': True, 'is_published': False}
    assert json.loads(response.content.decode('utf8')) == data
    admin_client.post(url)
    product.refresh_from_db()
    assert product.is_published


def test_view_product_not_deleted_before_confirmation(db, admin_client, product_in_stock):
    product = product_in_stock
    url = reverse('dashboard:product-delete', kwargs={'pk': product.pk})
    response = admin_client.get(url)
    assert response.status_code == HTTP_STATUS_OK
    product.refresh_from_db()


def test_view_product_delete(db, admin_client, product_in_stock):
    product = product_in_stock
    url = reverse('dashboard:product-delete', kwargs={'pk': product.pk})
    response = admin_client.post(url)
    assert response.status_code == HTTP_REDIRECTION
    assert not Product.objects.filter(pk=product.pk)


def test_view_product_class_not_deleted_before_confirmation(admin_client, product_in_stock):
    product_class = product_in_stock.product_class
    url = reverse('dashboard:product-class-delete', kwargs={'pk': product_class.pk})
    response = admin_client.get(url)
    assert response.status_code == HTTP_STATUS_OK
    assert ProductClass.objects.filter(pk=product_class.pk)


def test_view_product_class_delete(db, admin_client, product_in_stock):
    product_class = product_in_stock.product_class
    url = reverse('dashboard:product-class-delete', kwargs={'pk': product_class.pk})
    response = admin_client.post(url)
    assert response.status_code == HTTP_REDIRECTION
    assert not ProductClass.objects.filter(pk=product_class.pk)


def test_view_product_variant_not_deleted_before_confirmation(admin_client, product_in_stock):
    product_variant_pk = product_in_stock.variants.first().pk
    url = reverse('dashboard:variant-delete',
                  kwargs={'product_pk':product_in_stock.pk,
                          'variant_pk': product_variant_pk})
    response = admin_client.get(url)
    assert response.status_code == HTTP_STATUS_OK
    assert ProductVariant.objects.filter(pk=product_variant_pk)


def test_view_product_variant_delete(admin_client, product_in_stock):
    product_variant_pk = product_in_stock.variants.first().pk
    url = reverse('dashboard:variant-delete',
                  kwargs={'product_pk':product_in_stock.pk,
                          'variant_pk': product_variant_pk})
    response = admin_client.post(url)
    assert response.status_code == HTTP_REDIRECTION
    assert not ProductVariant.objects.filter(pk=product_variant_pk)


def test_view_stock_not_deleted_before_confirmation(admin_client, product_in_stock):
    product_variant = product_in_stock.variants.first()
    stock = Stock.objects.filter(variant=product_variant).first()
    url = reverse('dashboard:variant-stock-delete',
                  kwargs={'product_pk':product_in_stock.pk,
                          'variant_pk': product_variant.pk,
                          'stock_pk': stock.pk})
    response = admin_client.get(url)
    assert response.status_code == HTTP_STATUS_OK
    assert Stock.objects.filter(pk=stock.pk)


def test_view_stock_delete(admin_client, product_in_stock):
    product_variant = product_in_stock.variants.first()
    stock = Stock.objects.filter(variant=product_variant).first()
    url = reverse('dashboard:variant-stock-delete',
                  kwargs={'product_pk':product_in_stock.pk,
                          'variant_pk': product_variant.pk,
                          'stock_pk': stock.pk})
    response = admin_client.post(url)
    assert response.status_code == HTTP_REDIRECTION
    assert not Stock.objects.filter(pk=stock.pk)


def test_view_stock_location_not_deleted_before_confirmation(admin_client, stock_location):
    url = reverse('dashboard:product-stock-location-delete',
                  kwargs={'location_pk':stock_location.pk})
    response = admin_client.get(url)
    assert response.status_code == HTTP_STATUS_OK
    assert StockLocation.objects.filter(pk=stock_location.pk)


def test_view_stock_location_delete(admin_client, stock_location):
    url = reverse('dashboard:product-stock-location-delete',
                  kwargs={'location_pk':stock_location.pk})
    response = admin_client.post(url)
    assert response.status_code == HTTP_REDIRECTION
    assert not StockLocation.objects.filter(pk=stock_location.pk)


def test_view_attribute_not_deleted_before_confirmation(admin_client, color_attribute):
    url = reverse('dashboard:product-attribute-delete',
                  kwargs={'pk':color_attribute.pk})
    response = admin_client.get(url)
    assert response.status_code == HTTP_STATUS_OK
    assert ProductAttribute.objects.filter(pk=color_attribute.pk)


def test_view_attribute_delete(admin_client, color_attribute):
    url = reverse('dashboard:product-attribute-delete',
                  kwargs={'pk':color_attribute.pk})
    response = admin_client.post(url)
    assert response.status_code == HTTP_REDIRECTION
    assert not ProductAttribute.objects.filter(pk=color_attribute.pk)


def test_view_product_image_not_deleted_before_confirmation(admin_client, product_with_image):
    product_image = product_with_image.images.all()[0]
    url = reverse('dashboard:product-image-delete',
                  kwargs={'img_pk': product_image.pk,
                          'product_pk': product_with_image.pk})
    response = admin_client.get(url)
    assert response.status_code == HTTP_STATUS_OK
    assert ProductImage.objects.filter(pk=product_image.pk).count()


def test_view_product_image_delete(admin_client, product_with_image):
    product_image = product_with_image.images.all()[0]
    url = reverse('dashboard:product-image-delete',
                  kwargs={'img_pk': product_image.pk,
                          'product_pk': product_with_image.pk})
    response = admin_client.post(url)
    assert response.status_code == HTTP_REDIRECTION
    assert not ProductImage.objects.filter(pk=product_image.pk)
    
def test_view_reorder_product_images(admin_client, product_with_images):
    order_before = [img.pk for img in product_with_images.images.all()]
    ordered_images = list(reversed(order_before))
    url = reverse(
        'dashboard:product-images-reorder',
        kwargs={'product_pk': product_with_images.pk})
    data = {'ordered_images': ordered_images}
    response = admin_client.post(
        url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    order_after = [img.pk for img in product_with_images.images.all()]
    assert response.status_code == 200
    assert order_after == ordered_images


def test_view_invalid_reorder_product_images(
        admin_client, product_with_images):
    order_before = [img.pk for img in product_with_images.images.all()]
    ordered_images = list(reversed(order_before)).append(3)
    url = reverse(
        'dashboard:product-images-reorder',
        kwargs={'product_pk': product_with_images.pk})
    data = {'ordered_images': ordered_images}
    response = admin_client.post(
        url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 400
    resp_decoded = json.loads(response.content.decode('utf-8'))
    assert 'error' in resp_decoded
    assert 'ordered_images' in resp_decoded['error']
