from django.contrib.auth.models import Permission


GROUP_PERMISSIONS_MODELS = [
    'product.product',
    'product.category',
    'product.stock_location',
    'discount.sale',
    'discount.voucher',
    'order.order',
    'userprofile.user'
]


def get_permissions():
    codenames = []
    for group_permission in GROUP_PERMISSIONS_MODELS:
        model_name = group_permission.split('.')[1]
        codenames.append('view_%s' % model_name)
        codenames.append('edit_%s' % model_name)
    return Permission.objects.filter(codename__in=codenames)
