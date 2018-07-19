from django.contrib.auth.models import Permission

MODELS_PERMISSIONS = [
    'account.edit_user',
    'account.edit_staff',
    'account.impersonate_user',
    'discount.edit_sale',
    'discount.edit_voucher',
    'menu.edit_menu',
    'order.edit_order',
    'page.edit_page',
    'product.edit_category',
    'product.edit_product',
    'product.edit_properties',
    'shipping.edit_shipping',
    'site.edit_settings']


def get_permissions(permissions=None):
    if permissions is None:
        permissions = MODELS_PERMISSIONS
    codenames = [permission.split('.')[1] for permission in permissions]
    return Permission.objects.filter(codename__in=codenames).prefetch_related(
        'content_type').order_by('codename')
