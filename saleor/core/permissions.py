from django.contrib.auth.models import Permission


MODELS_PERMISSIONS = [
    'category.view_category',
    'category.edit_category',
    'order.view_order',
    'order.edit_order',
    'product.view_product',
    'product.edit_product',
    'sale.view_sale',
    'sale.edit_sale',
    'stock_location.view_stock_location',
    'stock_location.edit_stock_location',
    'user.view_user',
    'user.edit_user',
    'voucher.view_voucher',
    'voucher.edit_voucher',
]


def get_permissions():
    codenames = [permission.split('.')[1] for permission in MODELS_PERMISSIONS]
    return Permission.objects.filter(codename__in=codenames)
