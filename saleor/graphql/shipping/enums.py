import graphene

from ...shipping import ShippingMethodType

ShippingMethodTypeEnum = graphene.Enum(
    'ShippingMethodTypeEnum',
    [(code.upper(), code) for code, name in ShippingMethodType.CHOICES])
