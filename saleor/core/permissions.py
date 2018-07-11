from django.contrib.auth.models import Permission

MODELS_PERMISSIONS = [
    'account.view_user',
    'account.edit_user',
    'account.view_group',
    'account.edit_group',
    'account.view_staff',
    'account.edit_staff',
    'account.impersonate_user',
    'discount.view_sale',
    'discount.edit_sale',
    'discount.view_voucher',
    'discount.edit_voucher',
    'menu.view_menu',
    'menu.edit_menu',
    'order.view_order',
    'order.edit_order',
    'page.view_page',
    'page.edit_page',
    'product.view_category',
    'product.edit_category',
    'product.view_product',
    'product.edit_product',
    'product.view_properties',
    'product.edit_properties',
    'shipping.view_shipping',
    'shipping.edit_shipping',
    'site.edit_settings',
    'site.view_settings',
]


def get_permissions(permissions=None):
    if permissions is None:
        permissions = MODELS_PERMISSIONS
    codenames = [permission.split('.')[1] for permission in permissions]
    return Permission.objects.filter(codename__in=codenames).prefetch_related(
        'content_type').order_by('codename')
