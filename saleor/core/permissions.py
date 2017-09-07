from django.contrib.auth.models import Permission
from django.shortcuts import get_object_or_404

from saleor.userprofile.models import User


MODELS_PERMISSIONS = (('view', 'View Products in Dashboard'),
                      ('edit', 'Edit Product in Dashboard'))

PERMISSIONS = set([permission[0] for permission in MODELS_PERMISSIONS])


def get_user_permissions(user):
    form_data = {}
    permissions = Permission.objects.filter(user=user)
    for permission in permissions:
        if str(permission.content_type) not in form_data:
            form_data[str(permission.content_type)] = [permission.codename]
        else:
            form_data[str(permission.content_type)].append(permission.codename)
    return form_data


def update_permissions(user, pk, permissions):
    permissions = set(permissions)
    permissions_to_add = PERMISSIONS & permissions
    permissions_to_remove = PERMISSIONS - permissions

    add_permissions(permissions_to_add, user)
    remove_permissions(permissions_to_remove, user)

    queryset = User.objects.filter(is_staff=True)
    u = get_object_or_404(queryset, pk=pk)


def remove_permissions(permissions_to_remove, user):
    for permission in permissions_to_remove:
        permission = Permission.objects.get(codename=permission)
        user.user_permissions.remove(permission)


def add_permissions(permissions_to_add, user):
    for permission in permissions_to_add:
        permission = Permission.objects.get(codename=permission)
        user.user_permissions.add(permission)
