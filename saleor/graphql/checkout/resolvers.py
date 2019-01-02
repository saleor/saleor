from ...checkout import models


def resolve_checkout_lines(info, query):
    queryset = models.CartLine.objects.all()
    return queryset


def resolve_checkouts(info, query):
    queryset = models.Cart.objects.all()
    return queryset


def resolve_checkout(info, token):
    checkout = models.Cart.objects.filter(token=token).first()
    return checkout
