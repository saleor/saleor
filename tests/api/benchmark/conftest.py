import pytest

from saleor.checkout import calculations
from saleor.checkout.utils import add_variant_to_checkout
from saleor.discount.models import Sale
from saleor.menu.utils import update_menu
from saleor.payment import ChargeStatus, TransactionKind
from saleor.payment.models import Payment
from saleor.product.models import Category


@pytest.fixture
def site_with_top_menu(site_settings):
    menu = site_settings.top_menu
    menu.items.create(name="Link 1", url="http://example.com/")
    menu.items.create(name="Link 2", url="http://example.com/")
    menu.items.create(name="Link 3", url="http://example.com/")
    update_menu(menu)
    return site_settings


@pytest.fixture
def site_with_bottom_menu(site_settings):
    menu = site_settings.bottom_menu
    menu.items.create(name="Link 1", url="http://example.com/")
    menu.items.create(name="Link 2", url="http://example.com/")
    menu.items.create(name="Link 3", url="http://example.com/")
    update_menu(menu)
    return site_settings


@pytest.fixture
def sales_list():
    return list(
        Sale.objects.bulk_create(
            [Sale(name="Sale1", value=15), Sale(name="Sale2", value=5)]
        )
    )


@pytest.fixture
def homepage_collection(
    site_settings,
    collection,
    product_list_published,
    product_with_image,
    product_with_variant_with_two_attributes,
    product_with_multiple_values_attributes,
    product_without_shipping,
    non_default_category,
    sales_list,
):
    product_with_image.category = non_default_category
    product_with_image.save()

    collection.products.set(product_list_published)

    collection.products.add(product_with_image)
    collection.products.add(product_with_variant_with_two_attributes)
    collection.products.add(product_with_multiple_values_attributes)
    collection.products.add(product_without_shipping)

    site_settings.homepage_collection = collection
    site_settings.save(update_fields=["homepage_collection"])
    return collection


@pytest.fixture
def category_with_products(
    product_with_image,
    product_list_published,
    product_with_variant_with_two_attributes,
    product_with_multiple_values_attributes,
    product_without_shipping,
    sales_list,
):
    category = Category.objects.create(name="Category", slug="cat")

    product_list_published.update(category=category)

    product_with_image.category = category
    product_with_image.save()
    product_with_variant_with_two_attributes.category = category
    product_with_variant_with_two_attributes.save()
    product_with_multiple_values_attributes.category = category
    product_with_multiple_values_attributes.save()
    product_without_shipping.category = category
    product_without_shipping.save()

    return category


@pytest.fixture
def customer_checkout(customer_user, checkout_with_voucher_percentage_and_shipping):
    checkout_with_voucher_percentage_and_shipping.user = customer_user
    checkout_with_voucher_percentage_and_shipping.save()
    return checkout_with_voucher_percentage_and_shipping


@pytest.fixture()
def checkout_with_variant(checkout, stock):
    variant = stock.product_variant
    add_variant_to_checkout(checkout, variant, 1)

    checkout.save()
    return checkout


@pytest.fixture()
def checkout_with_shipping_address(checkout_with_variant, address):
    checkout = checkout_with_variant

    checkout.shipping_address = address.get_copy()
    checkout.save()

    return checkout


@pytest.fixture()
def checkout_with_shipping_method(checkout_with_shipping_address, shipping_method):
    checkout = checkout_with_shipping_address

    checkout.shipping_method = shipping_method
    checkout.save()

    return checkout


@pytest.fixture()
def checkout_with_billing_address(checkout_with_shipping_method, address):
    checkout = checkout_with_shipping_method

    checkout.billing_address = address
    checkout.save()

    return checkout


@pytest.fixture()
def checkout_with_charged_payment(checkout_with_billing_address):
    checkout = checkout_with_billing_address

    taxed_total = calculations.checkout_total(checkout=checkout, lines=list(checkout))
    payment = Payment.objects.create(
        gateway="mirumee.payments.dummy",
        is_active=True,
        total=taxed_total.gross.amount,
        currency="USD",
    )

    payment.charge_status = ChargeStatus.FULLY_CHARGED
    payment.captured_amount = payment.total
    payment.checkout = checkout_with_billing_address
    payment.save()

    payment.transactions.create(
        amount=payment.total,
        kind=TransactionKind.CAPTURE,
        gateway_response={},
        is_success=True,
    )

    return checkout
