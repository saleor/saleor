from django.contrib import messages
from django.utils.translation import ugettext as _
from satchless.item import InsufficientStock


def adjust_quantities(cart, request):
    cart_modified = False
    for cart_line in cart:
        try:
            cart.check_quantity(
                product=cart_line.product,
                quantity=cart_line.quantity,
                data=None)
        except InsufficientStock as e:
            cart.add(cart_line.product, quantity=int(e.item.stock),
                     replace=True)
            messages.warning(request,
                             _("Sorry, only %d pcs of %s remaining in stock. "
                               "Your order was changed" % (e.item.stock,
                                                           e.item)))
            cart_modified = True
    return cart_modified
