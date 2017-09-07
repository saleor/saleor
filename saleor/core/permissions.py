from django.contrib.auth.models import Permission
from django.shortcuts import get_object_or_404

from saleor.userprofile.models import User


MODELS_PERMISSIONS = [['view', 'View in Dashboard'],
                      ['edit', 'Edit in Dashboard']]


def get_user_permissions(user):
    form_data = {}
    permissions = Permission.objects.filter(user=user)
    for permission in permissions:
        if str(permission.content_type) not in form_data:
            form_data[str(permission.content_type)] = [permission.codename]
        else:
            form_data[str(permission.content_type)].append(permission.codename)
    return form_data


def update_permissions(user, pk, category, permissions):
    PERMISSIONS = set([permission[0] + "_" + category
                       for permission in MODELS_PERMISSIONS])
    permissions = set(permissions)
    permissions_to_add = PERMISSIONS & permissions
    permissions_to_remove = PERMISSIONS - permissions

    add_permissions(permissions_to_add, user)
    remove_permissions(permissions_to_remove, user)

    queryset = User.objects.filter(is_staff=True)
    u = get_object_or_404(queryset, pk=pk)


def add_permissions(permissions_to_add, user):
    for permission in permissions_to_add:
        permission = Permission.objects.get(codename=permission)
        user.user_permissions.add(permission)


def remove_permissions(permissions_to_remove, user):
    for permission in permissions_to_remove:
        permission = Permission.objects.get(codename=permission)
        user.user_permissions.remove(permission)


def build_permission_choices(cls):
    cls = cls.__name__.lower()
    choices = []
    for permission in MODELS_PERMISSIONS:
        choices.append((permission[0] + "_" + cls, permission[1]))
    return tuple(choices)
