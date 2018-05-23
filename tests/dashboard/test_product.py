import json
from io import BytesIO
from unittest.mock import MagicMock, Mock, patch

from django.conf import settings
from django.forms import HiddenInput
from django.forms.models import model_to_dict
from django.urls import reverse
from PIL import Image
from prices import Money, MoneyRange, TaxedMoney, TaxedMoneyRange
from tests.utils import get_redirect_location

from saleor.dashboard.product import ProductBulkAction
from saleor.dashboard.product.forms import ProductForm, ProductVariantForm
from saleor.product.forms import VariantChoiceField
from saleor.product.models import (
    AttributeChoiceValue, Collection, Product, ProductAttribute, ProductImage,
    ProductType, ProductVariant)
from ..utils import create_image


def test_view_product_list_with_filters(admin_client, product_list):
    url = reverse('dashboard:product-list')
    data = {
        'price_1': [''], 'price_0': [''], 'is_featured': [''],
        'name': ['Test'], 'sort_by': [''], 'is_published': ['']}

    response = admin_client.get(url, data)

    assert response.status_code == 200
    assert list(response.context['filter_set'].qs) == product_list


def test_view_product_list_with_filters_sort_by(admin_client, product_list):
    url = reverse('dashboard:product-list')
    data = {
        'price_1': [''], 'price_0': [''], 'is_featured': [''],
        'name': ['Test'], 'sort_by': ['name'], 'is_published': ['']}

    response = admin_client.get(url, data)

    assert response.status_code == 200
    assert list(response.context['filter_set'].qs) == product_list

    data['sort_by'] = ['-name']
    url = reverse('dashboard:product-list')

    response = admin_client.get(url, data)

    assert response.status_code == 200
    assert list(response.context['filter_set'].qs) == product_list[::-1]


def test_view_product_list_with_filters_is_published(
        admin_client, product_list, default_category):
    url = reverse('dashboard:product-list')
    data = {
        'price_1': [''], 'price_0': [''], 'is_featured': [''],
        'name': ['Test'], 'sort_by': ['name'], 'category': default_category.pk,
        'is_published': ['1']}

    response = admin_client.get(url, data)

    assert response.status_code == 200
    result = list(response.context['filter_set'].qs)
    assert result == [product_list[0], product_list[2]]


def test_view_product_list_with_filters_no_results(admin_client, product_list):
    url = reverse('dashboard:product-list')
    data = {
        'price_1': [''], 'price_0': [''], 'is_featured': [''],
        'name': ['BADTest'], 'sort_by': [''], 'is_published': ['']}

    response = admin_client.get(url, data)

    assert response.status_code == 200
    assert list(response.context['filter_set'].qs) == []


def test_view_product_list_pagination(admin_client, product_list):
    settings.DASHBOARD_PAGINATE_BY = 1
    url = reverse('dashboard:product-list')
    data = {'page': '1'}

    response = admin_client.get(url, data)

    assert response.status_code == 200
    assert not response.context['filter_set'].is_bound_unsorted

    data = {'page': '2'}

    response = admin_client.get(url, data)

    assert response.status_code == 200
    assert not response.context['filter_set'].is_bound_unsorted


def test_view_product_list_pagination_with_filters(admin_client, product_list):
    settings.DASHBOARD_PAGINATE_BY = 1
    url = reverse('dashboard:product-list')
    data = {
        'page': '1', 'price_1': [''], 'price_0': [''], 'is_featured': [''],
        'name': ['Test'], 'sort_by': ['name'], 'is_published': ['']}

    response = admin_client.get(url, data)

    assert response.status_code == 200
    assert list(response.context['products'])[0] == product_list[0]

    data['page'] = '2'

    response = admin_client.get(url, data)

    assert response.status_code == 200
    assert list(response.context['products'])[0] == product_list[1]


def test_view_product_details(admin_client, product):
    price = TaxedMoney(net=Money(10, 'USD'), gross=Money(10, 'USD'))
    sale_price = TaxedMoneyRange(start=price, stop=price)
    purchase_cost = MoneyRange(start=Money(1, 'USD'), stop=Money(1, 'USD'))
    url = reverse('dashboard:product-details', kwargs={'pk': product.pk})

    response = admin_client.get(url)

    assert response.status_code == 200
    context = response.context
    assert context['product'] == product
    assert context['sale_price'] == sale_price
    assert context['purchase_cost'] == purchase_cost
    assert context['margin'] == (90, 90)


def test_view_product_toggle_publish(db, admin_client, product):
    url = reverse('dashboard:product-publish', kwargs={'pk': product.pk})
    expected_response = {'success': True, 'is_published': False}

    response = admin_client.post(url)

    assert response.status_code == 200
    assert json.loads(response.content.decode('utf8')) == expected_response
    product.refresh_from_db()
    assert not product.is_published

    admin_client.post(url)

    product.refresh_from_db()
    assert product.is_published


def test_view_product_select_type_display_modal(admin_client):
    url = reverse('dashboard:product-add-select-type')
    response = admin_client.get(url)
    assert response.status_code == 200


def test_view_product_select_type(admin_client, product_type):
    url = reverse('dashboard:product-add-select-type')
    data = {'product_type': product_type.pk}

    response = admin_client.post(url, data)

    assert get_redirect_location(response) == reverse(
        'dashboard:product-add', kwargs={'type_pk': product_type.pk})
    assert response.status_code == 302


def test_view_product_select_type_by_ajax(admin_client, product_type):
    url = reverse('dashboard:product-add-select-type')
    data = {'product_type': product_type.pk}

    response = admin_client.post(
        url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    assert response.status_code == 200
    resp_decoded = json.loads(response.content.decode('utf-8'))
    assert resp_decoded.get('redirectUrl') == reverse(
        'dashboard:product-add', kwargs={'type_pk': product_type.pk})


def test_view_product_create(admin_client, product_type, default_category):
    url = reverse('dashboard:product-add', kwargs={'type_pk': product_type.pk})
    data = {
        'name': 'Product', 'description': 'This is product description.',
        'price': 10, 'category': default_category.pk, 'variant-sku': '123',
        'variant-quantity': 2}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    product = Product.objects.first()
    assert get_redirect_location(response) == reverse(
        'dashboard:product-details', kwargs={'pk': product.pk})
    assert Product.objects.count() == 1


def test_view_product_edit(admin_client, product):
    url = reverse('dashboard:product-update', kwargs={'pk': product.pk})
    data = {
        'name': 'Product second name', 'description': 'Product description.',
        'price': 10, 'category': product.category.pk, 'variant-sku': '123',
        'variant-quantity': 10}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    product.refresh_from_db()
    assert get_redirect_location(response) == reverse(
        'dashboard:product-details', kwargs={'pk': product.pk})
    assert product.name == 'Product second name'


def test_view_product_delete(db, admin_client, product):
    url = reverse('dashboard:product-delete', kwargs={'pk': product.pk})

    response = admin_client.post(url)

    assert response.status_code == 302
    assert not Product.objects.filter(pk=product.pk)


def test_view_product_not_deleted_before_confirmation(
        db, admin_client, product):
    url = reverse('dashboard:product-delete', kwargs={'pk': product.pk})

    response = admin_client.get(url)

    assert response.status_code == 200
    product.refresh_from_db()


def test_view_product_bulk_update_publish(admin_client, product_list):
    url = reverse('dashboard:product-bulk-update')
    products =  [product.pk for product in product_list]
    data = {'action': ProductBulkAction.PUBLISH, 'products': products}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    assert get_redirect_location(response) == reverse('dashboard:product-list')

    for p in product_list:
        p.refresh_from_db()
        assert p.is_published


def test_view_product_bulk_update_unpublish(admin_client, product_list):
    url = reverse('dashboard:product-bulk-update')
    products =  [product.pk for product in product_list]
    data = {'action': ProductBulkAction.UNPUBLISH, 'products': products}

    response = admin_client.post(url, data)


def test_product_variant_form(product):
    variant = product.variants.first()
    variant.name = ''
    variant.save()
    example_size = 'Small Size'
    data = {'attribute-size': example_size, 'sku': '1111', 'quantity': 2}
    form = ProductVariantForm(data, instance=variant)
    assert form.is_valid()
    form.save()
    variant.refresh_from_db()
    assert variant.name == example_size

    assert response.status_code == 302
    assert get_redirect_location(response) == reverse('dashboard:product-list')

    for p in product_list:
        p.refresh_from_db()
        assert not p.is_published


def test_view_ajax_products_list(admin_client, product):
    url = reverse('dashboard:ajax-products')

    response = admin_client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    assert response.status_code == 200
    resp_decoded = json.loads(response.content.decode('utf-8'))
    assert resp_decoded.get('results') == [
        {'id': product.id, 'text': str(product)}]


def test_view_product_type_list(admin_client, product_type):
    url = reverse('dashboard:product-type-list')

    response = admin_client.get(url)

    assert response.status_code == 200
    assert len(response.context['product_types']) == 1


def test_view_product_type_list_with_filters(admin_client, product_type):
    url = reverse('dashboard:product-type-list')
    data = {'name': ['Default Ty'], 'sort_by': ['']}

    response = admin_client.get(url, data)

    assert response.status_code == 200
    assert product_type in response.context['filter_set'].qs
    assert len(response.context['filter_set'].qs) == 1


def test_view_product_type_create(
        admin_client, color_attribute, size_attribute):
    url = reverse('dashboard:product-type-add')
    data = {
        'name': 'Testing Type',
        'product_attributes': [color_attribute.pk],
        'variant_attributes': [size_attribute.pk],
        'has_variants': True}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    assert get_redirect_location(response) == reverse(
        'dashboard:product-type-list')
    assert ProductType.objects.count() == 1


def test_view_product_type_create_invalid(
        admin_client, color_attribute, size_attribute):
    url = reverse('dashboard:product-type-add')
    # Don't allow same attribute in both fields
    data = {
        'name': 'Testing Type',
        'product_attributes': [size_attribute.pk],
        'variant_attributes': [color_attribute.pk, size_attribute.pk],
        'has_variants': True}

    response = admin_client.post(url, data)

    assert response.status_code == 200
    assert ProductType.objects.count() == 0


def test_view_product_type_create_missing_variant_attributes(
        admin_client, color_attribute, size_attribute):
    url = reverse('dashboard:product-type-add')
    data = {
        'name': 'Testing Type',
        'product_attributes': [color_attribute.pk],
        'variant_attributes': [size_attribute.pk],
        'has_variants': False}
    response = admin_client.post(url, data)

    assert response.status_code == 200
    assert ProductType.objects.count() == 0


def test_view_product_type_create_variantless(
        admin_client, color_attribute, size_attribute):
    url = reverse('dashboard:product-type-add')
    data = {
        'name': 'Testing Type',
        'product_attributes': [color_attribute.pk],
        'variant_attributes': [],
        'has_variants': False}
    response = admin_client.post(url, data)

    assert response.status_code == 302
    assert get_redirect_location(response) == reverse(
        'dashboard:product-type-list')
    assert ProductType.objects.count() == 1


def test_view_product_type_create_variantless_invalid(
        admin_client, color_attribute, size_attribute):
    url = reverse('dashboard:product-type-add')
    # Don't allow variant attributes when no variants
    data = {
        'name': 'Testing Type',
        'product_attributes': [color_attribute.pk],
        'variant_attributes': [size_attribute.pk],
        'has_variants': False}
    response = admin_client.post(url, data)

    assert response.status_code == 200
    assert ProductType.objects.count() == 0


def test_view_product_type_edit_to_no_variants_valid(admin_client, product):
    product_type = ProductType.objects.create(
        name='New product type', has_variants=True)
    product.product_type = product_type
    product.save()

    url = reverse(
        'dashboard:product-type-update', kwargs={'pk': product_type.pk})
    # When all products have only one variant you can change
    # has_variants to false
    data = {
        'name': product_type.name,
        'product_attributes': product_type.product_attributes.values_list(
            'pk', flat=True),
        'variant_attributes': product_type.variant_attributes.values_list(
            'pk', flat=True),
        'has_variants': False}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    assert get_redirect_location(response) == url
    product_type.refresh_from_db()
    assert not product_type.has_variants
    assert product.variants.count() == 1


def test_view_product_type_edit_to_no_variants_invalid(admin_client, product):
    product_type = ProductType.objects.create(
        name='New product type', has_variants=True)
    product.product_type = product_type
    product.save()

    product.variants.create(sku='12345')

    url = reverse(
        'dashboard:product-type-update', kwargs={'pk': product_type.pk})
    # Test has_variants validator which prevents turning off when product
    # has multiple variants
    data = {
        'name': product_type.name,
        'product_attributes': product_type.product_attributes.values_list(
            'pk', flat=True),
        'variant_attributes': product_type.variant_attributes.values_list(
            'pk', flat=True),
        'has_variants': False}

    response = admin_client.post(url, data)

    assert response.status_code == 200
    product_type.refresh_from_db()
    assert product_type.has_variants
    assert product.variants.count() == 2


def test_view_product_type_delete(db, admin_client, product):
    product_type = product.product_type
    url = reverse(
        'dashboard:product-type-delete', kwargs={'pk': product_type.pk})

    response = admin_client.post(url)

    assert response.status_code == 302
    assert not ProductType.objects.filter(pk=product_type.pk)


def test_view_product_type_not_deleted_before_confirmation(
        admin_client, product):
    product_type = product.product_type
    url = reverse(
        'dashboard:product-type-delete', kwargs={'pk': product_type.pk})

    response = admin_client.get(url)

    assert response.status_code == 200
    assert ProductType.objects.filter(pk=product_type.pk)


def test_view_product_variant_details(admin_client, product):
    product_type = product.product_type
    product_type.has_variants = True
    product_type.save()
    variant = product.variants.get()
    url = reverse(
        'dashboard:variant-details',
        kwargs={'product_pk': product.pk, 'variant_pk': variant.pk})

    response = admin_client.get(url)

    assert response.status_code == 200
    context = response.context
    assert context['product'] == product
    assert context['variant'] == variant
    assert context['images'].count() == 0
    assert context['margin'] == 90
    assert context['discounted_price'] == variant.base_price


def test_view_product_variant_details_redirect_to_product(
        admin_client, product):
    variant = product.variants.get()
    url = reverse(
        'dashboard:variant-details',
        kwargs={'product_pk': product.pk, 'variant_pk': variant.pk})

    response = admin_client.get(url)

    assert response.status_code == 302
    assert get_redirect_location(response) == reverse(
        'dashboard:product-details', kwargs={'pk': product.pk})


def test_view_product_variant_create(admin_client, product):
    product_type = product.product_type
    product_type.has_variants = True
    product_type.save()
    url = reverse('dashboard:variant-add', kwargs={'product_pk': product.pk})
    data = {
        'sku': 'ABC', 'price_override': '', 'quantity': 10, 'cost_price': ''}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    variant = product.variants.last()
    assert get_redirect_location(response) == reverse(
        'dashboard:variant-details',
        kwargs={'product_pk': product.pk, 'variant_pk': variant.pk})
    assert product.variants.count() == 2
    assert variant.sku == 'ABC'


def test_view_product_variant_edit(admin_client, product):
    variant = product.variants.get()
    url = reverse(
        'dashboard:variant-update',
        kwargs={'product_pk': product.pk, 'variant_pk': variant.pk})
    data = {
        'sku': 'ABC', 'price_override': '', 'quantity': 10, 'cost_price': ''}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    variant = product.variants.last()
    assert get_redirect_location(response) == reverse(
        'dashboard:variant-details',
        kwargs={'product_pk': product.pk, 'variant_pk': variant.pk})
    assert variant.sku == 'ABC'


def test_view_product_variant_delete(admin_client, product):
    variant = product.variants.get()
    url = reverse(
        'dashboard:variant-delete',
        kwargs={'product_pk': product.pk, 'variant_pk': variant.pk})

    response = admin_client.post(url)
    assert response.status_code == 302

    assert not ProductVariant.objects.filter(pk=variant.pk).exists()


def test_view_product_variant_not_deleted_before_confirmation(
        admin_client, product):
    variant = product.variants.get()
    url = reverse(
        'dashboard:variant-delete',
        kwargs={'product_pk': product.pk, 'variant_pk': variant.pk})

    response = admin_client.get(url)

    assert response.status_code == 200
    assert ProductVariant.objects.filter(pk=variant.pk).exists()


def test_view_variant_images(admin_client, product_with_image):
    variant = product_with_image.variants.get()
    product_image = product_with_image.images.get()
    url = reverse(
        'dashboard:variant-images',
        kwargs={'product_pk': product_with_image.pk, 'variant_pk': variant.pk})
    data = {'images': [product_image.pk]}

    response = admin_client.post(url, data)

    assert response.status_code == 302
    assert get_redirect_location(response) == reverse(
        'dashboard:variant-details',
        kwargs={'product_pk': product_with_image.pk, 'variant_pk': variant.pk})
    assert variant.variant_images.filter(image=product_image).exists()


def test_view_ajax_available_variants_list(
        admin_client, product, default_category):
    unavailable_product = Product.objects.create(
        name='Test product', price=10, product_type=product.product_type,
        category=default_category, is_published=False)
    unavailable_product.variants.create()
    url = reverse('dashboard:ajax-available-variants')

    response = admin_client.get(url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    assert response.status_code == 200
    resp_decoded = json.loads(response.content.decode('utf-8'))
    variant = product.variants.get()
    assert resp_decoded.get('results') == [
        {'id': variant.id, 'text': variant.get_ajax_label()}]


def test_view_product_images(admin_client, product_with_image):
    product_image = product_with_image.images.get()
    url = reverse(
        'dashboard:product-image-list',
        kwargs={'product_pk': product_with_image.pk})

    response = admin_client.get(url)

    assert response.status_code == 200
    assert response.context['product'] == product_with_image
    assert not response.context['is_empty']
    images = response.context['images']
    assert len(images) == 1
    assert product_image in images


def test_view_product_image_create(
        monkeypatch, admin_client, product_with_image):
    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        'saleor.dashboard.product.forms.create_product_thumbnails.delay',
        mock_create_thumbnails)
    url = reverse(
        'dashboard:product-image-add',
        kwargs={'product_pk': product_with_image.pk})

    response = admin_client.get(url)

    assert response.status_code == 200

    image, image_name = create_image()
    data = {'image_0': image, 'alt': ['description']}

    response = admin_client.post(url, data, follow=True)

    assert response.status_code == 200
    assert ProductImage.objects.count() == 2
    product_with_image.refresh_from_db()
    images = product_with_image.images.all()
    assert len(images) == 2
    assert image_name in images[1].image.name
    assert images[1].alt == 'description'
    mock_create_thumbnails.assert_called_once_with(images[1].pk)


def test_view_product_image_edit_same_image_add_description(
        monkeypatch, admin_client, product_with_image):
    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        'saleor.dashboard.product.forms.create_product_thumbnails.delay',
        mock_create_thumbnails)
    product_image = product_with_image.images.all()[0]
    url = reverse(
        'dashboard:product-image-update',
        kwargs={
            'img_pk': product_image.pk,
            'product_pk': product_with_image.pk})
    data = {'image_1': ['0.49x0.59'], 'alt': ['description']}

    response = admin_client.get(url)

    assert response.status_code == 200

    response = admin_client.post(url, data, follow=True)

    assert response.status_code == 200
    assert product_with_image.images.count() == 1
    product_image.refresh_from_db()
    assert product_image.alt == 'description'
    mock_create_thumbnails.assert_called_once_with(product_image.pk)


def test_view_product_image_edit_new_image(
        monkeypatch, admin_client, product_with_image):
    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        'saleor.dashboard.product.forms.create_product_thumbnails.delay',
        mock_create_thumbnails)
    product_image = product_with_image.images.all()[0]
    url = reverse(
        'dashboard:product-image-update',
        kwargs={
            'img_pk': product_image.pk,
            'product_pk': product_with_image.pk})

    response = admin_client.get(url)

    assert response.status_code == 200

    image, image_name = create_image()
    data = {'image_0': image, 'alt': ['description']}

    response = admin_client.post(url, data, follow=True)

    assert response.status_code == 200
    assert product_with_image.images.count() == 1
    product_image.refresh_from_db()
    assert image_name in product_image.image.name
    assert product_image.alt == 'description'
    mock_create_thumbnails.assert_called_once_with(product_image.pk)


def test_view_product_image_delete(admin_client, product_with_image):
    product_image = product_with_image.images.all()[0]
    url = reverse(
        'dashboard:product-image-delete',
        kwargs={
            'img_pk': product_image.pk,
            'product_pk': product_with_image.pk})

    response = admin_client.post(url)

    assert response.status_code == 302
    assert not ProductImage.objects.filter(pk=product_image.pk)


def test_view_product_image_not_deleted_before_confirmation(
        admin_client, product_with_image):
    product_image = product_with_image.images.all()[0]
    url = reverse(
        'dashboard:product-image-delete',
        kwargs={
            'img_pk': product_image.pk,
            'product_pk': product_with_image.pk})

    response = admin_client.get(url)

    assert response.status_code == 200
    assert ProductImage.objects.filter(pk=product_image.pk).count()


def test_view_ajax_reorder_product_images(admin_client, product_with_images):
    order_before = [img.pk for img in product_with_images.images.all()]
    ordered_images = list(reversed(order_before))
    url = reverse(
        'dashboard:product-images-reorder',
        kwargs={'product_pk': product_with_images.pk})
    data = {'ordered_images': ordered_images}

    response = admin_client.post(
        url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    assert response.status_code == 200
    order_after = [img.pk for img in product_with_images.images.all()]
    assert order_after == ordered_images


def test_view_ajax_reorder_product_images_invalid(
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


def test_view_ajax_upload_image(monkeypatch, admin_client, product_with_image):
    mock_create_thumbnails = Mock(return_value=None)
    monkeypatch.setattr(
        'saleor.dashboard.product.forms.create_product_thumbnails.delay',
        mock_create_thumbnails)
    product = product_with_image
    url = reverse(
        'dashboard:product-images-upload', kwargs={'product_pk': product.pk})
    image, image_name = create_image()
    data = {'image_0': image, 'alt': ['description']}

    response = admin_client.post(
        url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    assert response.status_code == 200
    assert ProductImage.objects.count() == 2
    product_with_image.refresh_from_db()
    images = product_with_image.images.all()
    assert len(images) == 2
    assert image_name in images[1].image.name
    mock_create_thumbnails.assert_called_once_with(images[1].pk)


def test_view_attribute_list(db, admin_client, color_attribute):
    url = reverse('dashboard:product-attributes')

    response = admin_client.get(url)

    assert response.status_code == 200
    result = response.context['attributes'].object_list
    assert len(result) == 1
    assert result[0][0] == color_attribute.pk
    assert result[0][1] == color_attribute.name
    assert len(result[0][2]) == 2
    assert not response.context['is_empty']


def test_view_attribute_details(admin_client, color_attribute):
    url = reverse(
        'dashboard:product-attribute-details',
        kwargs={'pk': color_attribute.pk})

    response = admin_client.get(url)

    assert response.status_code == 200
    assert response.context['attribute'] == color_attribute


def test_view_attribute_details_no_choices(admin_client):
    attribute = ProductAttribute.objects.create(slug='size', name='Size')
    url = reverse(
        'dashboard:product-attribute-details', kwargs={'pk': attribute.pk})

    response = admin_client.get(url)

    assert response.status_code == 200
    assert response.context['attribute'] == attribute


def test_view_attribute_create(admin_client, color_attribute):
    url = reverse('dashboard:product-attribute-add')
    data = {'name': 'test', 'slug': 'test'}

    response = admin_client.post(url, data, follow=True)

    assert response.status_code == 200
    assert ProductAttribute.objects.count() == 2


def test_view_attribute_create_not_valid(admin_client, color_attribute):
    url = reverse('dashboard:product-attribute-add')
    data = {}

    response = admin_client.post(url, data, follow=True)

    assert response.status_code == 200
    assert ProductAttribute.objects.count() == 1


def test_view_attribute_edit(color_attribute, admin_client):
    url = reverse(
        'dashboard:product-attribute-update',
        kwargs={'pk': color_attribute.pk})
    data = {'name': 'new_name', 'slug': 'new_slug'}

    response = admin_client.post(url, data, follow=True)

    assert response.status_code == 200
    assert ProductAttribute.objects.count() == 1
    color_attribute.refresh_from_db()
    assert color_attribute.name == 'new_name'
    assert color_attribute.slug == 'new_slug'


def test_view_attribute_delete(admin_client, color_attribute):
    url = reverse(
        'dashboard:product-attribute-delete',
        kwargs={'pk': color_attribute.pk})

    response = admin_client.post(url)

    assert response.status_code == 302
    assert not ProductAttribute.objects.filter(pk=color_attribute.pk).exists()


def test_view_attribute_not_deleted_before_confirmation(
        admin_client, color_attribute):
    url = reverse(
        'dashboard:product-attribute-delete',
        kwargs={'pk': color_attribute.pk})

    response = admin_client.get(url)

    assert response.status_code == 200
    assert ProductAttribute.objects.filter(pk=color_attribute.pk)


def test_view_attribute_choice_value_create(color_attribute, admin_client):
    values = AttributeChoiceValue.objects.filter(attribute=color_attribute.pk)
    assert values.count() == 2
    url = reverse(
        'dashboard:product-attribute-value-add',
        kwargs={'attribute_pk': color_attribute.pk})
    data = {'name': 'Pink', 'attribute': color_attribute.pk}

    response = admin_client.post(url, data, follow=True)

    assert response.status_code == 200
    values = AttributeChoiceValue.objects.filter(attribute=color_attribute.pk)
    assert values.count() == 3


def test_view_attribute_choice_value_create_invalid(
        color_attribute, admin_client):
    values = AttributeChoiceValue.objects.filter(attribute=color_attribute.pk)
    assert values.count() == 2
    url = reverse(
        'dashboard:product-attribute-value-add',
        kwargs={'attribute_pk': color_attribute.pk})
    data = {}

    response = admin_client.post(url, data, follow=True)

    assert response.status_code == 200
    values = AttributeChoiceValue.objects.filter(attribute=color_attribute.pk)
    assert values.count() == 2


def test_view_attribute_choice_value_edit(color_attribute, admin_client):
    values = AttributeChoiceValue.objects.filter(attribute=color_attribute.pk)
    assert values.count() == 2
    url = reverse(
        'dashboard:product-attribute-value-update',
        kwargs={'attribute_pk': color_attribute.pk, 'value_pk': values[0].pk})
    data = {'name': 'Pink', 'attribute': color_attribute.pk}

    response = admin_client.post(url, data, follow=True)

    assert response.status_code == 200
    values = AttributeChoiceValue.objects.filter(
        attribute=color_attribute.pk, name='Pink')
    assert len(values) == 1
    assert values[0].name == 'Pink'


def test_view_attribute_choice_value_delete(color_attribute, admin_client):
    values = AttributeChoiceValue.objects.filter(attribute=color_attribute.pk)
    assert values.count() == 2
    deleted_value = values[0]
    url = reverse(
        'dashboard:product-attribute-value-delete',
        kwargs={
            'attribute_pk': color_attribute.pk, 'value_pk': deleted_value.pk})

    response = admin_client.post(url, follow=True)

    assert response.status_code == 200
    values = AttributeChoiceValue.objects.filter(attribute=color_attribute.pk)
    assert len(values) == 1
    assert deleted_value not in values


def test_view_ajax_reorder_attribute_choice_values(
        admin_client, color_attribute):
    order_before = [val.pk for val in color_attribute.values.all()]
    ordered_values = list(reversed(order_before))
    url = reverse(
        'dashboard:product-attribute-values-reorder',
        kwargs={'attribute_pk': color_attribute.pk})
    data = {'ordered_values': ordered_values}
    response = admin_client.post(
        url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    order_after = [val.pk for val in color_attribute.values.all()]
    assert response.status_code == 200
    assert order_after == ordered_values


def test_view_ajax_reorder_attribute_choice_values_invalid(
        admin_client, color_attribute):
    order_before = [val.pk for val in color_attribute.values.all()]
    ordered_values = list(reversed(order_before)).append(3)
    url = reverse(
        'dashboard:product-attribute-values-reorder',
        kwargs={'attribute_pk': color_attribute.pk})
    data = {'ordered_values': ordered_values}
    response = admin_client.post(
        url, data, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 400
    resp_decoded = json.loads(response.content.decode('utf-8'))
    assert 'error' in resp_decoded
    assert 'ordered_values' in resp_decoded['error']


def test_get_formfield_name_with_unicode_characters(db):
    text_attribute = ProductAttribute.objects.create(
        slug='ąęαβδηθλμπ', name='ąęαβδηθλμπ')
    assert text_attribute.get_formfield_name() == 'attribute-ąęαβδηθλμπ'


def test_product_variant_form(product):
    variant = product.variants.first()
    variant.name = ''
    variant.save()
    example_size = 'Small Size'
    data = {'attribute-size': example_size, 'sku': '1111', 'quantity': 2}

    form = ProductVariantForm(data, instance=variant)
    assert form.is_valid()

    form.save()
    variant.refresh_from_db()
    assert variant.name == example_size


def test_hide_field_in_variant_choice_field_form():
    form = VariantChoiceField(Mock)
    variants, cart = MagicMock(), MagicMock()
    variants.count.return_value = 1
    variants.all()[0].pk = 'test'

    form.update_field_data(variants, discounts=None, taxes=None)

    assert isinstance(form.widget, HiddenInput)
    assert form.widget.attrs.get('value') == 'test'


def test_product_form_change_attributes(db, product, color_attribute):
    product_type = product.product_type
    text_attribute = ProductAttribute.objects.create(
        slug='author', name='Author')
    product_type.product_attributes.add(text_attribute)
    color_value = color_attribute.values.first()
    new_author = 'Main Tester'
    data = {
        'name': product.name,
        'price': product.price.amount,
        'category': product.category.pk,
        'description': 'description',
        'attribute-author': new_author,
        'attribute-color': color_value.pk}

    form = ProductForm(data, instance=product)
    assert form.is_valid()

    product = form.save()
    assert product.attributes[str(color_attribute.pk)] == str(color_value.pk)

    # Check that new attribute was created for author
    author_value = AttributeChoiceValue.objects.get(name=new_author)
    assert product.attributes[str(text_attribute.pk)] == str(author_value.pk)


def test_product_form_assign_collection_to_product(product):
    collection = Collection.objects.create(name='test_collections')
    data = {
        'name': product.name,
        'price': product.price.amount,
        'category': product.category.pk,
        'description': 'description',
        'collections': [collection.pk]}

    form = ProductForm(data, instance=product)
    assert form.is_valid()

    form.save()
    assert product.collections.first().name == 'test_collections'
    assert collection.products.first().name == product.name


def test_product_form_sanitize_product_description(
        product_type, default_category):
    product = Product.objects.create(
        name='Test Product', price=10, description='', pk=10,
        product_type=product_type, category=default_category)
    data = model_to_dict(product)
    data['description'] = (
        '<b>bold</b><p><i>italic</i></p><h2>Header</h2><h3>subheader</h3>'
        '<blockquote>quote</blockquote>'
        '<p><a href="www.mirumee.com">link</a></p>'
        '<p>an <script>evil()</script>example</p>')
    data['price'] = 20

    form = ProductForm(data, instance=product)
    assert form.is_valid()

    form.save()
    assert product.description == (
        '<b>bold</b><p><i>italic</i></p><h2>Header</h2><h3>subheader</h3>'
        '<blockquote>quote</blockquote>'
        '<p><a href="www.mirumee.com">link</a></p>'
        '<p>an &lt;script&gt;evil()&lt;/script&gt;example</p>')
    assert product.seo_description == (
        'bolditalicHeadersubheaderquotelinkan evil()example')


def test_product_form_seo_description(unavailable_product):
    seo_description = (
        'This is a dummy product. '
        'HTML <b>shouldn\'t be removed</b> since it\'s a simple text field.')
    data = model_to_dict(unavailable_product)
    data['price'] = 20
    data['description'] = 'a description'
    data['seo_description'] = seo_description

    form = ProductForm(data, instance=unavailable_product)
    assert form.is_valid()

    form.save()
    assert unavailable_product.seo_description == seo_description


def test_product_form_seo_description_too_long(unavailable_product):
    description = (
        'Saying it fourth made saw light bring beginning kind over herb '
        'won\'t creepeth multiply dry rule divided fish herb cattle greater '
        'fly divided midst, gathering can\'t moveth seed greater subdue. '
        'Lesser meat living fowl called. Dry don\'t wherein. Doesn\'t above '
        'form sixth. Image moving earth without forth light whales. Seas '
        'were first form fruit that form they\'re, shall air. And. Good of'
        'signs darkness be place. Was. Is form it. Whose. Herb signs stars '
        'fill own fruit wherein. '
        'Don\'t set man face living fifth Thing the whales were. '
        'You fish kind. '
        'Them, his under wherein place first you night gathering.')

    data = model_to_dict(unavailable_product)
    data['price'] = 20
    data['description'] = description

    form = ProductForm(data, instance=unavailable_product)
    assert form.is_valid()

    form.save()
    assert len(unavailable_product.seo_description) <= 300
    assert unavailable_product.seo_description == (
        'Saying it fourth made saw light bring beginning kind over herb '
        'won\'t creepeth multiply dry rule divided fish herb cattle greater '
        'fly divided midst, gathering can\'t moveth seed greater subdue. '
        'Lesser meat living fowl called. Dry don\'t wherein. Doesn\'t above '
        'form sixth. Image moving earth without f...')
