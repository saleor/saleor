from django.contrib.auth.models import Permission

MODELS_PERMISSIONS = [
    'account.manage_users',
    'account.manage_staff',
    'account.impersonate_users',
    'discount.manage_discounts',
    'menu.manage_menus',
    'order.manage_orders',
    'page.manage_pages',
    'product.manage_products',
    'shipping.manage_shipping',
    'site.manage_settings']


def get_permissions(permissions=None):
    if permissions is None:
        permissions = MODELS_PERMISSIONS
    codenames = [permission.split('.')[1] for permission in permissions]
    return Permission.objects.filter(codename__in=codenames).prefetch_related(
        'content_type').order_by('codename')
