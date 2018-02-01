import graphene
from django.shortcuts import reverse
from django.utils.translation import get_language, pgettext_lazy

from ...cart.models import Cart
from ...cart.utils import get_cart_from_request
from ...order.models import Order
from ...order.utils import create_groups_from_cart
from ...shipping.models import ShippingMethodCountry
from ...userprofile.models import Address
from .types import AddressInput, DetailsInput


def convert_address_input_to_model(address_input):
    """Converts AddressInput to Address model"""
    first_name, last_name = address_input.recipient.split(' ', 1)
    street_address_1 = address_input.address_line[0]
    data = {
        'first_name': first_name,
        'last_name': last_name,
        'company_name': address_input.organization,
        'street_address_1': street_address_1,
        'city': address_input.city,
        'postal_code': address_input.postal_code,
        'country': address_input.country,
        'country_area': address_input.region,
        'phone': address_input.phone}
    return Address(**data)


def create_order(cart, user, shipping_method, billing_address, shipping_address, discounts):
    total = cart.get_total(discounts=discounts)
    total += shipping_method.price

    order_data = {
        'language_code': get_language(), 'tracking_client_id': '',
        'shipping_price': shipping_method.price, 'total': total}

    if user.is_authenticated:
        order_data['user'] = user
        order_data['user_email'] = user.email

    if billing_address:
        billing_address = convert_address_input_to_model(billing_address)
        billing_address.save()
        order_data['billing_address'] = billing_address

    if shipping_address:
        shipping_address = convert_address_input_to_model(shipping_address)
        shipping_address.save()
        order_data['shipping_address'] = shipping_address

    order = Order.objects.create(**order_data)
    create_groups_from_cart(order, cart, shipping_method)
    cart.clear()

    order.create_history_entry(user=user, content=pgettext_lazy(
        'Order status history entry', 'Order was placed'))
    return order


class CreateOrderMutation(graphene.Mutation):
    class Arguments:
        details = DetailsInput()
        method_name = graphene.String()
        shipping_option = graphene.String()
        shipping_address = AddressInput()

    ok = graphene.Boolean()
    redirect_url = graphene.String()

    def mutate(self, info, details, method_name, shipping_option, shipping_address):
        request = info.context
        cart = get_cart_from_request(request, Cart.objects.for_display())
        shipping_method = ShippingMethodCountry.objects.get(pk=int(shipping_option))
        user = None if request.user.is_anonymous else request.user
        order = create_order(
            cart, user, shipping_method, details.billing_address,
            shipping_address, info.context.discounts)
        redirect_url = reverse(
            'order:checkout-success', kwargs={'token': order.token})
        return CreateOrderMutation(ok=True, redirect_url=redirect_url)
