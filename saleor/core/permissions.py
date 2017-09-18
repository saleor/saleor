from django.contrib.auth.models import Permission


MODELS_PERMISSIONS = [
    'product.view_product',
    'product.edit_product',
    'category.view_category',
    'category.edit_category',
    'stock_location.view_stock_location',
    'stock_location.edit_stock_location',
    'order.view_order',
    'order.edit_order',
    'sale.view_sale',
    'sale.edit_sale',
    'user.view_user',
    'user.edit_user',
    'voucher.view_voucher',
    'voucher.edit_voucher',
]


def get_permissions():
    codenames = [permission.split('.')[1] for permission in MODELS_PERMISSIONS]
    return Permission.objects.filter(codename__in=codenames)
