# import datetime
#
# from mock import Mock
# import pytest
#
# from django.core.urlresolvers import reverse
# from django.utils.encoding import smart_text
#
# from saleor.cart.models import Cart
# from saleor.cart import CartStatus, utils
# from saleor.product import models
# from saleor.product.utils import get_attributes_display_map
# from saleor.product.utils import get_availability
# from tests.utils import filter_products_by_attribute
#
#
# @pytest.fixture()
# def product_with_no_attributes(product_class):
#     product = models.Product.objects.create(
#         name='Test product', price='10.00',
#         product_class=product_class)
#     return product
#
#
# def test_stock_selector(product_in_stock):
#     variant = product_in_stock.variants.get()
#     preferred_stock = variant.select_stockrecord(5)
#     assert preferred_stock.quantity_available >= 5
#
#
# def test_stock_allocator(product_in_stock):
#     variant = product_in_stock.variants.get()
#     stock = variant.select_stockrecord(5)
#     assert stock.quantity_allocated == 0
#     models.Stock.objects.allocate_stock(stock, 1)
#     stock = models.Stock.objects.get(pk=stock.pk)
#     assert stock.quantity_allocated == 1
#
#
# def test_decrease_stock(product_in_stock):
#     stock = product_in_stock.variants.first().stock.first()
#     stock.quantity = 100
#     stock.quantity_allocated = 80
#     stock.save()
#     models.Stock.objects.decrease_stock(stock, 50)
#     stock.refresh_from_db()
#     assert stock.quantity == 50
#     assert stock.quantity_allocated == 30
#
#
# def test_deallocate_stock(product_in_stock):
#     stock = product_in_stock.variants.first().stock.first()
#     stock.quantity = 100
#     stock.quantity_allocated = 80
#     stock.save()
#     models.Stock.objects.deallocate_stock(stock, 50)
#     stock.refresh_from_db()
#     assert stock.quantity == 100
#     assert stock.quantity_allocated == 30
#
#
# def test_product_page_redirects_to_correct_slug(client, product_in_stock):
#     uri = product_in_stock.get_absolute_url()
#     uri = uri.replace(product_in_stock.get_slug(), 'spanish-inquisition')
#     response = client.get(uri)
#     assert response.status_code == 301
#     location = response['location']
#     if location.startswith('http'):
#         location = location.split('http://testserver')[1]
#     assert location == product_in_stock.get_absolute_url()
#
#
# def test_product_preview(admin_client, client, product_in_stock):
#     product_in_stock.available_on = (
#         datetime.date.today() + datetime.timedelta(days=7))
#     product_in_stock.save()
#     response = client.get(product_in_stock.get_absolute_url())
#     assert response.status_code == 404
#     response = admin_client.get(product_in_stock.get_absolute_url())
#     assert response.status_code == 200
#
#
# def test_availability(product_in_stock, monkeypatch, settings):
#     availability = get_availability(product_in_stock)
#     assert availability.price_range == product_in_stock.get_price_range()
#     assert availability.price_range_local_currency is None
#     monkeypatch.setattr(
#         'django_prices_openexchangerates.models.get_rates',
#         lambda c: {'PLN': Mock(rate=2)})
#     settings.DEFAULT_COUNTRY = 'PL'
#     settings.OPENEXCHANGERATES_API_KEY = 'fake-key'
#     availability = get_availability(product_in_stock, local_currency='PLN')
#     assert availability.price_range_local_currency.min_price.currency == 'PLN'
#     assert availability.available
#
#
# def test_filtering_by_attribute(db, color_attribute):
#     product_class_a = models.ProductClass.objects.create(
#         name='New class', has_variants=True)
#     product_class_a.product_attributes.add(color_attribute)
#     product_class_b = models.ProductClass.objects.create(name='New class',
#                                                          has_variants=True)
#     product_class_b.variant_attributes.add(color_attribute)
#     product_a = models.Product.objects.create(
#         name='Test product a', price=10,
#         product_class=product_class_a)
#     models.ProductVariant.objects.create(product=product_a, sku='1234')
#     product_b = models.Product.objects.create(
#         name='Test product b', price=10,
#         product_class=product_class_b)
#     variant_b = models.ProductVariant.objects.create(product=product_b,
#                                                      sku='12345')
#     color = color_attribute.values.first()
#     color_2 = color_attribute.values.last()
#     product_a.set_attribute(color_attribute.pk, color.pk)
#     product_a.save()
#     variant_b.set_attribute(color_attribute.pk, color.pk)
#     variant_b.save()
#
#     filtered = filter_products_by_attribute(models.Product.objects.all(),
#                                             color_attribute.pk, color.pk)
#     assert product_a in list(filtered)
#     assert product_b in list(filtered)
#
#     product_a.set_attribute(color_attribute.pk, color_2.pk)
#     product_a.save()
#     filtered = filter_products_by_attribute(models.Product.objects.all(),
#                                             color_attribute.pk, color.pk)
#     assert product_a not in list(filtered)
#     assert product_b in list(filtered)
#     filtered = filter_products_by_attribute(models.Product.objects.all(),
#                                             color_attribute.pk, color_2.pk)
#     assert product_a in list(filtered)
#     assert product_b not in list(filtered)
#
#
# def test_view_invalid_add_to_cart(client, product_in_stock, request_cart):
#     variant = product_in_stock.variants.get()
#     request_cart.add(variant, 2)
#     response = client.post(
#         reverse(
#             'product:add-to-cart',
#             kwargs={
#                 'slug': product_in_stock.get_slug(),
#                 'product_id': product_in_stock.pk}),
#         {})
#     assert response.status_code == 200
#     assert request_cart.quantity == 2
#
#
# def test_view_add_to_cart(client, product_in_stock, request_cart):
#     variant = product_in_stock.variants.get()
#     request_cart.add(variant, 1)
#     response = client.post(
#         reverse(
#             'product:add-to-cart',
#             kwargs={'slug': product_in_stock.get_slug(),
#                     'product_id': product_in_stock.pk}),
#         {'quantity': 1, 'variant': variant.pk})
#     assert response.status_code == 302
#     assert request_cart.quantity == 1
#
#
# def test_adding_to_cart_with_current_user_token(
#         admin_user, admin_client, product_in_stock):
#     client = admin_client
#     key = utils.COOKIE_NAME
#     cart = Cart.objects.create(user=admin_user)
#     variant = product_in_stock.variants.first()
#     cart.add(variant, 1)
#
#     response = client.get('/cart/')
#     utils.set_cart_cookie(cart, response)
#     client.cookies[key] = response.cookies[key]
#
#     client.post(
#         reverse('product:add-to-cart',
#                 kwargs={'slug': product_in_stock.get_slug(),
#                         'product_id': product_in_stock.pk}),
#         {'quantity': 1, 'variant': variant.pk})
#
#     assert Cart.objects.count() == 1
#     assert Cart.objects.get(user=admin_user).pk == cart.pk
#
#
# def test_adding_to_cart_with_another_user_token(
#         admin_user, admin_client, product_in_stock, customer_user):
#     client = admin_client
#     key = utils.COOKIE_NAME
#     cart = Cart.objects.create(user=customer_user)
#     variant = product_in_stock.variants.first()
#     cart.add(variant, 1)
#
#     response = client.get('/cart/')
#     utils.set_cart_cookie(cart, response)
#     client.cookies[key] = response.cookies[key]
#
#     client.post(
#         reverse('product:add-to-cart',
#                 kwargs={'slug': product_in_stock.get_slug(),
#                         'product_id': product_in_stock.pk}),
#         {'quantity': 1, 'variant': variant.pk})
#
#     assert Cart.objects.count() == 2
#     assert Cart.objects.get(user=admin_user).pk != cart.pk
#
#
# def test_anonymous_adding_to_cart_with_another_user_token(
#         client, product_in_stock, customer_user):
#     key = utils.COOKIE_NAME
#     cart = Cart.objects.create(user=customer_user)
#     variant = product_in_stock.variants.first()
#     cart.add(variant, 1)
#
#     response = client.get('/cart/')
#     utils.set_cart_cookie(cart, response)
#     client.cookies[key] = response.cookies[key]
#
#     client.post(
#         reverse('product:add-to-cart',
#                 kwargs={'slug': product_in_stock.get_slug(),
#                         'product_id': product_in_stock.pk}),
#         {'quantity': 1, 'variant': variant.pk})
#
#     assert Cart.objects.count() == 2
#     assert Cart.objects.get(user=None).pk != cart.pk
#
#
# def test_adding_to_cart_with_deleted_cart_token(
#         admin_user, admin_client, product_in_stock):
#     client = admin_client
#     key = utils.COOKIE_NAME
#     cart = Cart.objects.create(user=admin_user)
#     old_token = cart.token
#     variant = product_in_stock.variants.first()
#     cart.add(variant, 1)
#
#     response = client.get('/cart/')
#     utils.set_cart_cookie(cart, response)
#     client.cookies[key] = response.cookies[key]
#     cart.delete()
#
#     client.post(
#         reverse('product:add-to-cart',
#                 kwargs={'slug': product_in_stock.get_slug(),
#                         'product_id': product_in_stock.pk}),
#         {'quantity': 1, 'variant': variant.pk})
#
#     assert Cart.objects.count() == 1
#     assert not Cart.objects.filter(token=old_token).exists()
#
#
# def test_adding_to_cart_with_closed_cart_token(
#         admin_user, admin_client, product_in_stock):
#     client = admin_client
#     key = utils.COOKIE_NAME
#     cart = Cart.objects.create(user=admin_user)
#     variant = product_in_stock.variants.first()
#     cart.add(variant, 1)
#     cart.change_status(CartStatus.ORDERED)
#
#     response = client.get('/cart/')
#     utils.set_cart_cookie(cart, response)
#     client.cookies[key] = response.cookies[key]
#
#     client.post(
#         reverse('product:add-to-cart',
#                 kwargs={'slug': product_in_stock.get_slug(),
#                         'product_id': product_in_stock.pk}),
#         {'quantity': 1, 'variant': variant.pk})
#
#     assert Cart.objects.filter(
#         user=admin_user, status=CartStatus.OPEN).count() == 1
#     assert Cart.objects.filter(
#         user=admin_user, status=CartStatus.ORDERED).count() == 1
#
#
# def test_get_attributes_display_map(product_in_stock):
#     attributes = product_in_stock.product_class.product_attributes.all()
#     attributes_display_map = get_attributes_display_map(
#         product_in_stock, attributes)
#
#     product_attr = product_in_stock.product_class.product_attributes.first()
#     attr_value = product_attr.values.first()
#
#     assert len(attributes_display_map) == 1
#     assert attributes_display_map == {product_attr.pk: attr_value}
#
#
# def test_get_attributes_display_map_empty(product_with_no_attributes):
#     product = product_with_no_attributes
#     attributes = product.product_class.product_attributes.all()
#
#     assert get_attributes_display_map(product, attributes) == {}
#
#
# def test_get_attributes_display_map_no_choices(product_in_stock):
#     attributes = product_in_stock.product_class.product_attributes.all()
#     product_attr = attributes.first()
#
#     product_in_stock.set_attribute(product_attr.pk, -1)
#     attributes_display_map = get_attributes_display_map(
#         product_in_stock, attributes)
#
#     assert attributes_display_map == {product_attr.pk: smart_text(-1)}
