from ...checkout import models


def resolve_checkout_lines(info, query):
    queryset = models.CartLine.objects.all()
    return queryset


def resolve_checkouts(info, query):
    queryset = models.Cart.objects.all()
    return queryset
