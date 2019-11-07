import uuid
from decimal import Decimal
from io import BytesIO
from typing import List
from unittest.mock import MagicMock, Mock

import pytest
from django.contrib.auth.models import Permission
from django.contrib.sites.models import Site
from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import ModelForm
from django.test.client import Client
from django_countries import countries
from PIL import Image
from prices import Money, TaxedMoney

from saleor.account.backends import BaseBackend
from saleor.account.models import Address, ServiceAccount, User
from saleor.checkout import utils
from saleor.checkout.models import Checkout
from saleor.checkout.utils import add_variant_to_checkout
from saleor.core.payments import PaymentInterface
from saleor.discount import DiscountInfo, DiscountValueType, VoucherType
from saleor.discount.models import Sale, Voucher, VoucherCustomer, VoucherTranslation
from saleor.giftcard.models import GiftCard
from saleor.menu.models import Menu, MenuItem
from saleor.menu.utils import update_menu
from saleor.order import OrderStatus
from saleor.order.actions import fulfill_order_line
from saleor.order.events import OrderEvents
from saleor.order.models import FulfillmentStatus, Order, OrderEvent
from saleor.order.utils import recalculate_order
from saleor.page.models import Page, PageTranslation
from saleor.payment import ChargeStatus, TransactionKind
from saleor.payment.models import Payment
from saleor.product import AttributeInputType
from saleor.product.models import (
    Attribute,
    AttributeTranslation,
    AttributeValue,
    AttributeValueTranslation,
    Category,
    CategoryTranslation,
    Collection,
    CollectionTranslation,
    DigitalContent,
    DigitalContentUrl,
    Product,
    ProductImage,
    ProductTranslation,
    ProductType,
    ProductVariant,
    ProductVariantTranslation,
)
from saleor.product.utils.attributes import associate_attribute_values_to_instance
from saleor.shipping.models import ShippingMethod, ShippingMethodType, ShippingZone
from saleor.site import AuthenticationBackends
from saleor.site.models import AuthorizationKey, SiteSettings
from saleor.webhook import WebhookEventType
from saleor.webhook.models import Webhook
from tests.utils import create_image


@pytest.fixture(autouse=True)
def setup_dummy_gateway(settings):
    settings.PLUGINS = ["saleor.payment.gateways.dummy.plugin.DummyGatewayPlugin"]
    return settings


@pytest.fixture(autouse=True)
def site_settings(db, settings) -> SiteSettings:
    """Create a site and matching site settings.

    This fixture is autouse because django.contrib.sites.models.Site and
    saleor.site.models.SiteSettings have a one-to-one relationship and a site
    should never exist without a matching settings object.
    """
    site = Site.objects.get_or_create(name="mirumee.com", domain="mirumee.com")[0]
    obj = SiteSettings.objects.get_or_create(
        site=site,
        default_mail_sender_name="Mirumee Labs",
        default_mail_sender_address="mirumee@example.com",
    )[0]
    settings.SITE_ID = site.pk

    main_menu = Menu.objects.get_or_create(
        name=settings.DEFAULT_MENUS["top_menu_name"]
    )[0]
    update_menu(main_menu)
    secondary_menu = Menu.objects.get_or_create(
        name=settings.DEFAULT_MENUS["bottom_menu_name"]
    )[0]
    update_menu(secondary_menu)
    obj.top_menu = main_menu
    obj.bottom_menu = secondary_menu
    obj.save()
    return obj


@pytest.fixture
def checkout(db):
    return Checkout.objects.create()


@pytest.fixture
def checkout_with_item(checkout, product):
    variant = product.variants.get()
    add_variant_to_checkout(checkout, variant, 3)
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_single_item(checkout, product):
    variant = product.variants.get()
    add_variant_to_checkout(checkout, variant, 1)
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_items(checkout, product_list, product):
    variant = product.variants.get()
    add_variant_to_checkout(checkout, variant, 1)
    for prod in product_list:
        variant = prod.variants.get()
        add_variant_to_checkout(checkout, variant, 1)
    return checkout


@pytest.fixture
def checkout_with_voucher(checkout, product, voucher):
    variant = product.variants.get()
    add_variant_to_checkout(checkout, variant, 3)
    checkout.voucher_code = voucher.code
    checkout.discount = Money("20.00", "USD")
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_voucher_percentage(checkout, product, voucher_percentage):
    variant = product.variants.get()
    add_variant_to_checkout(checkout, variant, 3)
    checkout.voucher_code = voucher_percentage.code
    checkout.discount = Money("3.00", "USD")
    checkout.save()
    return checkout


@pytest.fixture
def checkout_with_gift_card(checkout_with_item, gift_card):
    checkout_with_item.gift_cards.add(gift_card)
    checkout_with_item.save()
    return checkout_with_item


@pytest.fixture
def checkout_with_voucher_percentage_and_shipping(
    checkout_with_voucher_percentage, shipping_method, address
):
    checkout = checkout_with_voucher_percentage
    checkout.shipping_method = shipping_method
    checkout.shipping_address = address
    checkout.save()
    return checkout


@pytest.fixture
def address(db):  # pylint: disable=W0613
    return Address.objects.create(
        first_name="John",
        last_name="Doe",
        company_name="Mirumee Software",
        street_address_1="Tęczowa 7",
        city="WROCŁAW",
        postal_code="53-601",
        country="PL",
        phone="+48713988102",
    )


@pytest.fixture
def address_other_country():
    return Address.objects.create(
        first_name="John",
        last_name="Doe",
        street_address_1="4371 Lucas Knoll Apt. 791",
        city="BENNETTMOUTH",
        postal_code="13377",
        country="IS",
        phone="",
    )


@pytest.fixture
def address_usa():
    return Address.objects.create(
        first_name="John",
        last_name="Doe",
        street_address_1="2000 Main Street",
        city="Irvine",
        postal_code="92614",
        country_area="CA",
        country="US",
        phone="",
    )


@pytest.fixture
def graphql_address_data():
    return {
        "firstName": "John Saleor",
        "lastName": "Doe Mirumee",
        "companyName": "Mirumee Software",
        "streetAddress1": "Tęczowa 7",
        "streetAddress2": "",
        "postalCode": "53-601",
        "country": "PL",
        "city": "Wrocław",
        "countryArea": "",
        "phone": "+48321321888",
    }


@pytest.fixture
def customer_user(address):  # pylint: disable=W0613
    default_address = address.get_copy()
    user = User.objects.create_user(
        "test@example.com",
        "password",
        default_billing_address=default_address,
        default_shipping_address=default_address,
        first_name="Leslie",
        last_name="Wade",
    )
    user.addresses.add(default_address)
    return user


@pytest.fixture
def user_checkout(customer_user):
    return Checkout.objects.get_or_create(user=customer_user)[0]


@pytest.fixture
def request_checkout(checkout, monkeypatch):
    # FIXME: Fixtures should not have any side effects
    monkeypatch.setattr(
        utils,
        "get_checkout_from_request",
        lambda request, checkout_queryset=None: checkout,
    )
    return checkout


@pytest.fixture
def request_checkout_with_item(product, request_checkout):
    variant = product.variants.get()
    add_variant_to_checkout(request_checkout, variant)
    return request_checkout


@pytest.fixture
def order(customer_user):
    address = customer_user.default_billing_address.get_copy()
    return Order.objects.create(
        billing_address=address, user_email=customer_user.email, user=customer_user
    )


@pytest.fixture
def admin_user(db):
    """Return a Django admin user."""
    return User.objects.create_superuser("admin@example.com", "password")


@pytest.fixture
def admin_client(admin_user):
    """Return a Django test client logged in as an admin user."""
    client = Client()
    client.login(username=admin_user.email, password="password")
    return client


@pytest.fixture
def staff_user(db):
    """Return a staff member."""
    return User.objects.create_user(
        email="staff_test@example.com",
        password="password",
        is_staff=True,
        is_active=True,
    )


@pytest.fixture
def staff_client(client, staff_user):
    """Return a Django test client logged in as an staff member."""
    client.login(username=staff_user.email, password="password")
    return client


@pytest.fixture
def authorized_client(client, customer_user):
    client.login(username=customer_user.email, password="password")
    return client


@pytest.fixture
def shipping_zone(db):  # pylint: disable=W0613
    shipping_zone = ShippingZone.objects.create(
        name="Europe", countries=[code for code, name in countries]
    )
    shipping_zone.shipping_methods.create(
        name="DHL",
        minimum_order_price=Money(0, "USD"),
        type=ShippingMethodType.PRICE_BASED,
        price=Money(10, "USD"),
        shipping_zone=shipping_zone,
    )
    return shipping_zone


@pytest.fixture
def shipping_zone_without_countries(db):  # pylint: disable=W0613
    shipping_zone = ShippingZone.objects.create(name="Europe", countries=[])
    shipping_zone.shipping_methods.create(
        name="DHL",
        minimum_order_price=Money(0, "USD"),
        type=ShippingMethodType.PRICE_BASED,
        price=Money(10, "USD"),
        shipping_zone=shipping_zone,
    )
    return shipping_zone


@pytest.fixture
def shipping_method(shipping_zone):
    return ShippingMethod.objects.create(
        name="DHL",
        minimum_order_price=Money(0, "USD"),
        type=ShippingMethodType.PRICE_BASED,
        price=Money(10, "USD"),
        shipping_zone=shipping_zone,
    )


@pytest.fixture
def color_attribute(db):  # pylint: disable=W0613
    attribute = Attribute.objects.create(slug="color", name="Color")
    AttributeValue.objects.create(attribute=attribute, name="Red", slug="red")
    AttributeValue.objects.create(attribute=attribute, name="Blue", slug="blue")
    return attribute


@pytest.fixture
def color_attribute_without_values(db):  # pylint: disable=W0613
    return Attribute.objects.create(slug="color", name="Color")


@pytest.fixture
def pink_attribute_value(color_attribute):  # pylint: disable=W0613
    value = AttributeValue.objects.create(
        slug="pink", name="Pink", attribute=color_attribute, value="#FF69B4"
    )
    return value


@pytest.fixture
def size_attribute(db):  # pylint: disable=W0613
    attribute = Attribute.objects.create(slug="size", name="Size")
    AttributeValue.objects.create(attribute=attribute, name="Small", slug="small")
    AttributeValue.objects.create(attribute=attribute, name="Big", slug="big")
    return attribute


@pytest.fixture
def attribute_list() -> List[Attribute]:
    return list(
        Attribute.objects.bulk_create(
            [
                Attribute(slug="size", name="Size"),
                Attribute(slug="weight", name="Weight"),
                Attribute(slug="thickness", name="Thickness"),
            ]
        )
    )


@pytest.fixture
def image():
    img_data = BytesIO()
    image = Image.new("RGB", size=(1, 1))
    image.save(img_data, format="JPEG")
    return SimpleUploadedFile("product.jpg", img_data.getvalue())


@pytest.fixture
def category(db):  # pylint: disable=W0613
    return Category.objects.create(name="Default", slug="default")


@pytest.fixture
def category_with_image(db, image, media_root):  # pylint: disable=W0613
    return Category.objects.create(
        name="Default", slug="default", background_image=image
    )


@pytest.fixture
def categories_tree(db, product_type):  # pylint: disable=W0613
    parent = Category.objects.create(name="Parent", slug="parent")
    parent.children.create(name="Child", slug="child")
    child = parent.children.first()

    product_attr = product_type.product_attributes.first()
    attr_value = product_attr.values.first()

    product = Product.objects.create(
        name="Test product",
        price=Money(10, "USD"),
        product_type=product_type,
        category=child,
    )

    associate_attribute_values_to_instance(product, product_attr, attr_value)
    return parent


@pytest.fixture
def non_default_category(db):  # pylint: disable=W0613
    return Category.objects.create(name="Not default", slug="not-default")


@pytest.fixture
def permission_manage_discounts():
    return Permission.objects.get(codename="manage_discounts")


@pytest.fixture
def permission_manage_gift_card():
    return Permission.objects.get(codename="manage_gift_card")


@pytest.fixture
def permission_manage_orders():
    return Permission.objects.get(codename="manage_orders")


@pytest.fixture
def permission_manage_plugins():
    return Permission.objects.get(codename="manage_plugins")


@pytest.fixture
def permission_manage_service_accounts():
    return Permission.objects.get(codename="manage_service_accounts")


@pytest.fixture
def product_type(color_attribute, size_attribute):
    product_type = ProductType.objects.create(
        name="Default Type", has_variants=True, is_shipping_required=True
    )
    product_type.product_attributes.add(color_attribute)
    product_type.variant_attributes.add(size_attribute)
    return product_type


@pytest.fixture
def product_type_without_variant():
    product_type = ProductType.objects.create(
        name="Type", has_variants=False, is_shipping_required=True
    )
    return product_type


@pytest.fixture
def product(product_type, category):
    product_attr = product_type.product_attributes.first()
    product_attr_value = product_attr.values.first()

    product = Product.objects.create(
        name="Test product",
        price=Money("10.00", "USD"),
        product_type=product_type,
        category=category,
    )

    associate_attribute_values_to_instance(product, product_attr, product_attr_value)

    variant_attr = product_type.variant_attributes.first()
    variant_attr_value = variant_attr.values.first()

    variant = ProductVariant.objects.create(
        product=product,
        sku="123",
        cost_price=Money("1.00", "USD"),
        quantity=10,
        quantity_allocated=1,
    )

    associate_attribute_values_to_instance(variant, variant_attr, variant_attr_value)
    return product


@pytest.fixture
def product_with_two_variants(color_attribute, size_attribute, category):
    product_type = ProductType.objects.create(
        name="Type with two variants", has_variants=True, is_shipping_required=True
    )
    product_type.variant_attributes.add(color_attribute)
    product_type.variant_attributes.add(size_attribute)

    product = Product.objects.create(
        name="Test product with two variants",
        price=Money("10.00", "USD"),
        product_type=product_type,
        category=category,
    )

    variant = ProductVariant.objects.create(
        product=product,
        sku="prodVar1",
        cost_price=Money("1.00", "USD"),
        quantity=10,
        quantity_allocated=1,
    )

    associate_attribute_values_to_instance(
        variant, color_attribute, color_attribute.values.first()
    )
    associate_attribute_values_to_instance(
        variant, size_attribute, size_attribute.values.first()
    )

    return product


@pytest.fixture
def product_with_multiple_values_attributes(product, product_type, category) -> Product:

    attribute = Attribute.objects.create(
        slug="modes", name="Available Modes", input_type=AttributeInputType.MULTISELECT
    )

    attr_val_1 = AttributeValue.objects.create(
        attribute=attribute, name="Eco Mode", slug="eco"
    )
    attr_val_2 = AttributeValue.objects.create(
        attribute=attribute, name="Performance Mode", slug="power"
    )

    product_type.product_attributes.clear()
    product_type.product_attributes.add(attribute)

    associate_attribute_values_to_instance(product, attribute, attr_val_1, attr_val_2)
    return product


@pytest.fixture
def product_with_default_variant(product_type_without_variant, category):
    product = Product.objects.create(
        name="Test product",
        price=Money(10, "USD"),
        product_type=product_type_without_variant,
        category=category,
    )
    ProductVariant.objects.create(
        product=product, sku="1234", track_inventory=True, quantity=100
    )
    return product


@pytest.fixture
def variant(product):
    product_variant = ProductVariant.objects.create(
        product=product,
        sku="SKU_A",
        cost_price=Money(1, "USD"),
        quantity=5,
        quantity_allocated=3,
    )
    return product_variant


@pytest.fixture
def product_variant_list(product):
    return list(
        ProductVariant.objects.bulk_create(
            [
                ProductVariant(product=product, sku="1"),
                ProductVariant(product=product, sku="2"),
                ProductVariant(product=product, sku="3"),
            ]
        )
    )


@pytest.fixture
def product_without_shipping(category):
    product_type = ProductType.objects.create(
        name="Type with no shipping", has_variants=False, is_shipping_required=False
    )
    product = Product.objects.create(
        name="Test product",
        price=Money("10.00", "USD"),
        product_type=product_type,
        category=category,
    )
    ProductVariant.objects.create(product=product, sku="SKU_B")
    return product


@pytest.fixture
def product_list(product_type, category):
    product_attr = product_type.product_attributes.first()
    attr_value = product_attr.values.first()

    products = list(
        Product.objects.bulk_create(
            [
                Product(
                    pk=1486,
                    name="Test product 1",
                    price=Money(10, "USD"),
                    category=category,
                    product_type=product_type,
                    is_published=True,
                ),
                Product(
                    pk=1487,
                    name="Test product 2",
                    price=Money(20, "USD"),
                    category=category,
                    product_type=product_type,
                    is_published=False,
                ),
                Product(
                    pk=1489,
                    name="Test product 3",
                    price=Money(20, "USD"),
                    category=category,
                    product_type=product_type,
                    is_published=True,
                ),
            ]
        )
    )
    ProductVariant.objects.bulk_create(
        [
            ProductVariant(
                product=products[0],
                sku=str(uuid.uuid4()).replace("-", ""),
                track_inventory=True,
                quantity=100,
            ),
            ProductVariant(
                product=products[1],
                sku=str(uuid.uuid4()).replace("-", ""),
                track_inventory=True,
                quantity=100,
            ),
            ProductVariant(
                product=products[2],
                sku=str(uuid.uuid4()).replace("-", ""),
                track_inventory=True,
                quantity=100,
            ),
        ]
    )

    for product in products:
        associate_attribute_values_to_instance(product, product_attr, attr_value)

    return products


@pytest.fixture
def product_list_unpublished(product_list):
    products = Product.objects.filter(pk__in=[product.pk for product in product_list])
    products.update(is_published=False)
    return products


@pytest.fixture
def product_list_published(product_list):
    products = Product.objects.filter(pk__in=[product.pk for product in product_list])
    products.update(is_published=True)
    return products


@pytest.fixture
def order_list(customer_user):
    address = customer_user.default_billing_address.get_copy()
    data = {
        "billing_address": address,
        "user": customer_user,
        "user_email": customer_user.email,
    }
    order = Order.objects.create(**data)
    order1 = Order.objects.create(**data)
    order2 = Order.objects.create(**data)

    return [order, order1, order2]


@pytest.fixture
def product_with_image(product, image, media_root):
    ProductImage.objects.create(product=product, image=image)
    return product


@pytest.fixture
def unavailable_product(product_type, category):
    product = Product.objects.create(
        name="Test product",
        price=Money("10.00", "USD"),
        product_type=product_type,
        is_published=False,
        category=category,
    )
    return product


@pytest.fixture
def unavailable_product_with_variant(product_type, category):
    product = Product.objects.create(
        name="Test product",
        price=Money("10.00", "USD"),
        product_type=product_type,
        is_published=False,
        category=category,
    )

    variant_attr = product_type.variant_attributes.first()
    variant_attr_value = variant_attr.values.first()

    variant = ProductVariant.objects.create(
        product=product,
        sku="123",
        cost_price=Money(1, "USD"),
        quantity=10,
        quantity_allocated=1,
    )

    associate_attribute_values_to_instance(variant, variant_attr, variant_attr_value)
    return product


@pytest.fixture
def product_with_images(product_type, category, media_root):
    product = Product.objects.create(
        name="Test product",
        price=Money("10.00", "USD"),
        product_type=product_type,
        category=category,
    )
    file_mock_0 = MagicMock(spec=File, name="FileMock0")
    file_mock_0.name = "image0.jpg"
    file_mock_1 = MagicMock(spec=File, name="FileMock1")
    file_mock_1.name = "image1.jpg"
    product.images.create(image=file_mock_0)
    product.images.create(image=file_mock_1)
    return product


@pytest.fixture
def voucher(db):  # pylint: disable=W0613
    return Voucher.objects.create(code="mirumee", discount_value=20)


@pytest.fixture
def voucher_percentage(db):
    return Voucher.objects.create(
        code="mirumee",
        discount_value=10,
        discount_value_type=DiscountValueType.PERCENTAGE,
    )


@pytest.fixture
def voucher_specific_product_type(voucher_percentage):
    voucher_percentage.type = VoucherType.SPECIFIC_PRODUCT
    voucher_percentage.save()
    return voucher_percentage


@pytest.fixture
def voucher_with_high_min_spent_amount():
    return Voucher.objects.create(
        code="mirumee", discount_value=10, min_spent=Money(1000000, "USD")
    )


@pytest.fixture
def voucher_shipping_type():
    return Voucher.objects.create(
        code="mirumee", discount_value=10, type=VoucherType.SHIPPING, countries="IS"
    )


@pytest.fixture
def voucher_free_shipping(voucher_percentage):
    voucher_percentage.type = VoucherType.SHIPPING
    voucher_percentage.discount_value = 100
    voucher_percentage.save()
    return voucher_percentage


@pytest.fixture
def voucher_customer(voucher, customer_user):
    email = customer_user.email
    return VoucherCustomer.objects.create(voucher=voucher, customer_email=email)


@pytest.fixture()
def order_line(order, variant):
    net = variant.get_price()
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    return order.lines.create(
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        quantity=3,
        variant=variant,
        unit_price=TaxedMoney(net=net, gross=gross),
        tax_rate=23,
    )


@pytest.fixture
def gift_card(customer_user, staff_user):
    return GiftCard.objects.create(
        code="mirumee_giftcard",
        user=customer_user,
        initial_balance=Money(10, "USD"),
        current_balance=Money(10, "USD"),
    )


@pytest.fixture
def gift_card_used(staff_user):
    return GiftCard.objects.create(
        code="gift_card_used",
        initial_balance=Money(150, "USD"),
        current_balance=Money(100, "USD"),
    )


@pytest.fixture
def gift_card_created_by_staff(staff_user):
    return GiftCard.objects.create(
        code="mirumee_staff",
        initial_balance=Money(5, "USD"),
        current_balance=Money(5, "USD"),
    )


@pytest.fixture()
def order_with_lines(order, product_type, category, shipping_zone):
    product = Product.objects.create(
        name="Test product",
        price=Money("10.00", "USD"),
        product_type=product_type,
        category=category,
    )
    variant = ProductVariant.objects.create(
        product=product,
        sku="SKU_A",
        cost_price=Money(1, "USD"),
        quantity=5,
        quantity_allocated=3,
    )
    net = variant.get_price()
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    order.lines.create(
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        quantity=3,
        variant=variant,
        unit_price=TaxedMoney(net=net, gross=gross),
        tax_rate=23,
    )

    product = Product.objects.create(
        name="Test product 2",
        price=Money("20.00", "USD"),
        product_type=product_type,
        category=category,
    )
    variant = ProductVariant.objects.create(
        product=product,
        sku="SKU_B",
        cost_price=Money(2, "USD"),
        quantity=2,
        quantity_allocated=2,
    )

    net = variant.get_price()
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    order.lines.create(
        product_name=str(variant.product),
        variant_name=str(variant),
        product_sku=variant.sku,
        is_shipping_required=variant.is_shipping_required(),
        quantity=2,
        variant=variant,
        unit_price=TaxedMoney(net=net, gross=gross),
        tax_rate=23,
    )

    order.shipping_address = order.billing_address.get_copy()
    method = shipping_zone.shipping_methods.get()
    order.shipping_method_name = method.name
    order.shipping_method = method

    net = method.get_total()
    gross = Money(amount=net.amount * Decimal(1.23), currency=net.currency)
    order.shipping_price = TaxedMoney(net=net, gross=gross)
    order.save()

    recalculate_order(order)

    order.refresh_from_db()
    return order


@pytest.fixture
def order_events(order):
    for event_type, _ in OrderEvents.CHOICES:
        OrderEvent.objects.create(type=event_type, order=order)


@pytest.fixture
def fulfilled_order(order_with_lines):
    order = order_with_lines
    fulfillment = order.fulfillments.create()
    line_1 = order.lines.first()
    line_2 = order.lines.last()
    fulfillment.lines.create(order_line=line_1, quantity=line_1.quantity)
    fulfill_order_line(line_1, line_1.quantity)
    fulfillment.lines.create(order_line=line_2, quantity=line_2.quantity)
    fulfill_order_line(line_2, line_2.quantity)
    order.status = OrderStatus.FULFILLED
    order.save(update_fields=["status"])
    return order


@pytest.fixture
def fulfilled_order_with_cancelled_fulfillment(fulfilled_order):
    fulfillment = fulfilled_order.fulfillments.create()
    line_1 = fulfilled_order.lines.first()
    line_2 = fulfilled_order.lines.last()
    fulfillment.lines.create(order_line=line_1, quantity=line_1.quantity)
    fulfillment.lines.create(order_line=line_2, quantity=line_2.quantity)
    fulfillment.status = FulfillmentStatus.CANCELED
    fulfillment.save()
    return fulfilled_order


@pytest.fixture
def fulfillment(fulfilled_order):
    return fulfilled_order.fulfillments.first()


@pytest.fixture
def draft_order(order_with_lines):
    order_with_lines.status = OrderStatus.DRAFT
    order_with_lines.save(update_fields=["status"])
    return order_with_lines


@pytest.fixture
def payment_txn_preauth(order_with_lines, payment_dummy):
    order = order_with_lines
    payment = payment_dummy
    payment.order = order
    payment.save()

    payment.transactions.create(
        amount=payment.total,
        kind=TransactionKind.AUTH,
        gateway_response={},
        is_success=True,
    )
    return payment


@pytest.fixture
def payment_txn_captured(order_with_lines, payment_dummy):
    order = order_with_lines
    payment = payment_dummy
    payment.order = order
    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.save()

    payment.transactions.create(
        amount=payment.total,
        kind=TransactionKind.CAPTURE,
        gateway_response={},
        is_success=True,
    )
    return payment


@pytest.fixture
def payment_txn_refunded(order_with_lines, payment_dummy):
    order = order_with_lines
    payment = payment_dummy
    payment.order = order
    payment.charge_status = ChargeStatus.FULLY_REFUNDED
    payment.is_active = False
    payment.save()

    payment.transactions.create(
        amount=payment.total,
        kind=TransactionKind.REFUND,
        gateway_response={},
        is_success=True,
    )
    return payment


@pytest.fixture
def payment_not_authorized(payment_dummy):
    payment_dummy.is_active = False
    payment_dummy.save()
    return payment_dummy


@pytest.fixture
def sale(product, category, collection):
    sale = Sale.objects.create(name="Sale", value=5)
    sale.products.add(product)
    sale.categories.add(category)
    sale.collections.add(collection)
    return sale


@pytest.fixture
def discount_info(category, collection, sale):
    return DiscountInfo(
        sale=sale,
        product_ids=set(),
        category_ids={category.id},  # assumes this category does not have children
        collection_ids={collection.id},
    )


@pytest.fixture
def authorization_backend_name():
    return AuthenticationBackends.FACEBOOK


@pytest.fixture
def authorization_key(site_settings, authorization_backend_name):
    return AuthorizationKey.objects.create(
        site_settings=site_settings,
        name=authorization_backend_name,
        key="Key",
        password="Password",
    )


@pytest.fixture
def base_backend(authorization_backend_name):
    base_backend = BaseBackend()
    base_backend.DB_NAME = authorization_backend_name
    return base_backend


@pytest.fixture
def permission_manage_staff():
    return Permission.objects.get(codename="manage_staff")


@pytest.fixture
def permission_manage_products():
    return Permission.objects.get(codename="manage_products")


@pytest.fixture
def permission_manage_shipping():
    return Permission.objects.get(codename="manage_shipping")


@pytest.fixture
def permission_manage_users():
    return Permission.objects.get(codename="manage_users")


@pytest.fixture
def permission_manage_settings():
    return Permission.objects.get(codename="manage_settings")


@pytest.fixture
def permission_impersonate_users():
    return Permission.objects.get(codename="impersonate_users")


@pytest.fixture
def permission_manage_menus():
    return Permission.objects.get(codename="manage_menus")


@pytest.fixture
def permission_manage_pages():
    return Permission.objects.get(codename="manage_pages")


@pytest.fixture
def permission_manage_translations():
    return Permission.objects.get(codename="manage_translations")


@pytest.fixture
def permission_manage_webhooks():
    return Permission.objects.get(codename="manage_webhooks")


@pytest.fixture
def collection(db):
    collection = Collection.objects.create(
        name="Collection",
        slug="collection",
        is_published=True,
        description="Test description",
    )
    return collection


@pytest.fixture
def collection_with_products(db, collection, product_list_published):
    collection.products.set(list(product_list_published))
    return product_list_published


@pytest.fixture
def collection_with_image(db, image, media_root):
    collection = Collection.objects.create(
        name="Collection",
        slug="collection",
        description="Test description",
        background_image=image,
    )
    return collection


@pytest.fixture
def collection_list(db):
    collections = Collection.objects.bulk_create(
        [
            Collection(name="Collection 1"),
            Collection(name="Collection 2"),
            Collection(name="Collection 3"),
        ]
    )
    return collections


@pytest.fixture
def collection_list_unpublished(collection_list):
    collections = Collection.objects.filter(
        pk__in=[collection.pk for collection in collection_list]
    )
    collections.update(is_published=False)
    return collections


@pytest.fixture
def draft_collection(db):
    collection = Collection.objects.create(
        name="Draft collection", slug="draft-collection", is_published=False
    )
    return collection


@pytest.fixture
def unpublished_collection():
    collection = Collection.objects.create(
        name="Unpublished collection", slug="unpublished-collection", is_published=False
    )
    return collection


@pytest.fixture
def page(db):
    data = {"slug": "test-url", "title": "Test page", "content": "test content"}
    page = Page.objects.create(**data)
    return page


@pytest.fixture
def page_list(db):
    data_1 = {"slug": "test-url", "title": "Test page", "content": "test content"}
    data_2 = {"slug": "test-url-2", "title": "Test page", "content": "test content"}
    pages = Page.objects.bulk_create([Page(**data_1), Page(**data_2)])
    return pages


@pytest.fixture
def page_list_unpublished(db):
    pages = Page.objects.bulk_create(
        [
            Page(slug="page-1", title="Page 1", is_published=False),
            Page(slug="page-2", title="Page 2", is_published=False),
            Page(slug="page-3", title="Page 3", is_published=False),
        ]
    )
    return pages


@pytest.fixture
def model_form_class():
    mocked_form_class = MagicMock(name="test", spec=ModelForm)
    mocked_form_class._meta = Mock(name="_meta")
    mocked_form_class._meta.model = "test_model"
    mocked_form_class._meta.fields = "test_field"
    return mocked_form_class


@pytest.fixture
def menu(db):
    return Menu.objects.get_or_create(name="test-navbar", json_content={})[0]


@pytest.fixture
def menu_item(menu):
    item = MenuItem.objects.create(menu=menu, name="Link 1", url="http://example.com/")
    update_menu(menu)
    return item


@pytest.fixture
def menu_item_list(menu):
    menu_item_1 = MenuItem.objects.create(menu=menu, name="Link 1")
    menu_item_2 = MenuItem.objects.create(menu=menu, name="Link 2")
    menu_item_3 = MenuItem.objects.create(menu=menu, name="Link 3")
    update_menu(menu)
    return menu_item_1, menu_item_2, menu_item_3


@pytest.fixture
def menu_with_items(menu, category, collection):
    menu.items.create(name="Link 1", url="http://example.com/")
    menu_item = menu.items.create(name="Link 2", url="http://example.com/")
    menu.items.create(name=category.name, category=category, parent=menu_item)
    menu.items.create(name=collection.name, collection=collection, parent=menu_item)
    update_menu(menu)
    return menu


@pytest.fixture
def translated_variant_fr(product):
    attribute = product.product_type.variant_attributes.first()
    return AttributeTranslation.objects.create(
        language_code="fr", attribute=attribute, name="Name tranlsated to french"
    )


@pytest.fixture
def translated_attribute(product):
    attribute = product.product_type.product_attributes.first()
    return AttributeTranslation.objects.create(
        language_code="fr", attribute=attribute, name="French attribute name"
    )


@pytest.fixture
def translated_attribute_value(pink_attribute_value):
    return AttributeValueTranslation.objects.create(
        language_code="fr",
        attribute_value=pink_attribute_value,
        name="French attribute value name",
    )


@pytest.fixture
def voucher_translation_fr(voucher):
    return VoucherTranslation.objects.create(
        language_code="fr", voucher=voucher, name="French name"
    )


@pytest.fixture
def product_translation_fr(product):
    return ProductTranslation.objects.create(
        language_code="fr",
        product=product,
        name="French name",
        description="French description",
    )


@pytest.fixture
def variant_translation_fr(variant):
    return ProductVariantTranslation.objects.create(
        language_code="fr", product_variant=variant, name="French product variant name"
    )


@pytest.fixture
def collection_translation_fr(collection):
    return CollectionTranslation.objects.create(
        language_code="fr",
        collection=collection,
        name="French collection name",
        description="French description",
    )


@pytest.fixture
def category_translation_fr(category):
    return CategoryTranslation.objects.create(
        language_code="fr",
        category=category,
        name="French category name",
        description="French category description",
    )


@pytest.fixture
def page_translation_fr(page):
    return PageTranslation.objects.create(
        language_code="fr",
        page=page,
        title="French page title",
        content="French page content",
    )


@pytest.fixture
def payment_dummy(db, order_with_lines):
    return Payment.objects.create(
        gateway="Dummy",
        order=order_with_lines,
        is_active=True,
        cc_first_digits="4111",
        cc_last_digits="1111",
        cc_brand="VISA",
        cc_exp_month=12,
        cc_exp_year=2027,
        total=order_with_lines.total.gross.amount,
        currency=order_with_lines.total.gross.currency,
        billing_first_name=order_with_lines.billing_address.first_name,
        billing_last_name=order_with_lines.billing_address.last_name,
        billing_company_name=order_with_lines.billing_address.company_name,
        billing_address_1=order_with_lines.billing_address.street_address_1,
        billing_address_2=order_with_lines.billing_address.street_address_2,
        billing_city=order_with_lines.billing_address.city,
        billing_postal_code=order_with_lines.billing_address.postal_code,
        billing_country_code=order_with_lines.billing_address.country.code,
        billing_country_area=order_with_lines.billing_address.country_area,
        billing_email=order_with_lines.user_email,
    )


@pytest.fixture
def digital_content(category, media_root) -> DigitalContent:
    product_type = ProductType.objects.create(
        name="Digital Type",
        has_variants=True,
        is_shipping_required=False,
        is_digital=True,
    )
    product = Product.objects.create(
        name="Test digital product",
        price=Money("10.00", "USD"),
        product_type=product_type,
        category=category,
    )
    product_variant = ProductVariant.objects.create(
        product=product,
        sku="SKU_554",
        cost_price=Money(1, "USD"),
        quantity=5,
        quantity_allocated=3,
    )

    assert product_variant.is_digital()

    image_file, image_name = create_image()
    d_content = DigitalContent.objects.create(
        content_file=image_file,
        product_variant=product_variant,
        use_default_settings=True,
    )
    return d_content


@pytest.fixture
def digital_content_url(digital_content, order_line):
    return DigitalContentUrl.objects.create(content=digital_content, line=order_line)


@pytest.fixture
def media_root(tmpdir, settings):
    settings.MEDIA_ROOT = str(tmpdir.mkdir("media"))


@pytest.fixture
def description_json():
    return {
        "blocks": [
            {
                "key": "",
                "data": {},
                "text": "E-commerce for the PWA era",
                "type": "header-two",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {},
                "text": (
                    "A modular, high performance e-commerce storefront "
                    "built with GraphQL, Django, and ReactJS."
                ),
                "type": "unstyled",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {},
                "text": "",
                "type": "unstyled",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {},
                "text": (
                    "Saleor is a rapidly-growing open source e-commerce platform "
                    "that has served high-volume companies from branches "
                    "like publishing and apparel since 2012. Based on Python "
                    "and Django, the latest major update introduces a modular "
                    "front end with a GraphQL API and storefront and dashboard "
                    "written in React to make Saleor a full-functionality "
                    "open source e-commerce."
                ),
                "type": "unstyled",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {},
                "text": "",
                "type": "unstyled",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {},
                "text": "Get Saleor today!",
                "type": "unstyled",
                "depth": 0,
                "entityRanges": [{"key": 0, "length": 17, "offset": 0}],
                "inlineStyleRanges": [],
            },
        ],
        "entityMap": {
            "0": {
                "data": {"href": "https://github.com/mirumee/saleor"},
                "type": "LINK",
                "mutability": "MUTABLE",
            }
        },
    }


@pytest.fixture
def description_raw():
    return """\
E-commerce for the PWA era
A modular, high performance e-commerce storefront built with GraphQL, Django, \
and ReactJS.

Saleor is a rapidly-growing open source e-commerce platform that has served \
high-volume companies from branches like publishing and apparel since 2012. \
Based on Python and Django, the latest major update introduces a modular \
front end with a GraphQL API and storefront and dashboard written in React \
to make Saleor a full-functionality open source e-commerce.

Get Saleor today!"""


@pytest.fixture
def other_description_json():
    return {
        "blocks": [
            {
                "key": "",
                "data": {},
                "text": "A GRAPHQL-FIRST ECOMMERCE PLATFORM FOR PERFECTIONISTS",
                "type": "header-two",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
            {
                "key": "",
                "data": {},
                "text": (
                    "Saleor is powered by a GraphQL server running on "
                    "top of Python 3 and a Django 2 framework."
                ),
                "type": "unstyled",
                "depth": 0,
                "entityRanges": [],
                "inlineStyleRanges": [],
            },
        ],
        "entityMap": {},
    }


@pytest.fixture
def other_description_raw():
    return (
        "A GRAPHQL-FIRST ECOMMERCE PLATFORM FOR PERFECTIONISTS\n"
        "Saleor is powered by a GraphQL server running on top of Python 3 "
        "and a Django 2 framework."
    )


@pytest.fixture
def service_account(db):
    return ServiceAccount.objects.create(name="Sample service account", is_active=True)


@pytest.fixture
def webhook(service_account):
    webhook = Webhook.objects.create(
        service_account=service_account, target_url="http://www.example.com/test"
    )
    webhook.events.create(event_type=WebhookEventType.ORDER_CREATED)
    return webhook


@pytest.fixture
def fake_payment_interface(mocker):
    return mocker.Mock(spec=PaymentInterface)


@pytest.fixture
def mock_get_manager(mocker, fake_payment_interface):
    mgr = mocker.patch(
        "saleor.payment.gateway.get_extensions_manager",
        autospec=True,
        return_value=fake_payment_interface,
    )
    yield fake_payment_interface
    mgr.assert_called_once()
