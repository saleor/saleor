from ...checkout import models


def resolve_checkout_lines():
    queryset = models.CheckoutLine.objects.all()
    return queryset


def resolve_checkouts():
    queryset = models.Checkout.objects.all()
    return queryset


def resolve_checkout(token):
    return models.Checkout.objects.filter(token=token).first()
