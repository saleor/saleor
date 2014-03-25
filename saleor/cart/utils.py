from django.utils.translation import ugettext as _
from satchless.item import InsufficientStock


def cart_is_ready_to_checkout(cart):
    checkout_possible = True
    for cartline in cart:
        variant_class = cartline.product.__class__
        variant = variant_class.objects.get(pk=cartline.product.pk)
        try:
            cart.check_quantity(
                product=variant,
                quantity=cartline.quantity,
                data=None)
        except InsufficientStock as e:
            cartline.error = _(
                "Sorry, only %d remaining in stock." % e.item.stock)
            checkout_possible = False

    return checkout_possible

