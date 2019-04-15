from ...checkout import models


def resolve_checkout_lines():
    queryset = models.CartLine.objects.all()
    return queryset


def resolve_checkouts():
    queryset = models.Cart.objects.all()
    return queryset


def resolve_checkout(token):
    checkout = models.Cart.objects.filter(token=token).first()
    return checkout
