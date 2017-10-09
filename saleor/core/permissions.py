from __future__ import unicode_literals
from django.contrib.auth.models import Permission


MODELS_PERMISSIONS = [
    'order.view_order',
    'order.edit_order',
    'product.view_category',
    'product.edit_category',
    'product.view_product',
    'product.edit_product',
    'product.view_stock_location',
    'product.edit_stock_location',
    'sale.view_sale',
    'sale.edit_sale',
    'user.view_user',
    'user.edit_user',
    'voucher.view_voucher',
    'voucher.edit_voucher',
]


def get_permissions():
    codenames = [permission.split('.')[1] for permission in MODELS_PERMISSIONS]
    return Permission.objects.filter(codename__in=codenames)\
        .prefetch_related('content_type')
