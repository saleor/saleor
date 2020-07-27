from ...core.anonymize import obfuscate_address, obfuscate_email


def obfuscate_order(order):
    order.user_email = obfuscate_email(order.user_email)
    if order.shipping_address:
        order.shipping_address = obfuscate_address(order.shipping_address)
        order.shipping_address.save()
    if order.billing_address:
        order.billing_address = obfuscate_address(order.billing_address)
        order.billing_address.save()
    return order
