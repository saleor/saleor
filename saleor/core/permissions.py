from django.contrib.auth.models import Permission
from django.shortcuts import get_object_or_404

from saleor.userprofile.models import User


PERMISSIONS_CHOICES = [['view', 'View'],
                       ['edit', 'Edit']]


def get_user_permissions(user):
    form_data = {}
    permissions = Permission.objects.filter(user=user)
    for permission in permissions:
        category = standarize_name(permission)
        if category not in form_data:
            form_data[category] = [permission.codename]
        else:
            form_data[category].append(permission.codename)
    return form_data


def standarize_name(permission):
    return str(permission.content_type).replace(' ', '_').lower()


def update_permissions(user, category, permissions):
    PERMISSIONS = set([permission[0] + "_" + category
                       for permission in PERMISSIONS_CHOICES])
    permissions = set(permissions)
    permissions_to_add = PERMISSIONS & permissions
    permissions_to_remove = PERMISSIONS - permissions

    add_permissions(permissions_to_add, user)
    remove_permissions(permissions_to_remove, user)

    queryset = User.objects.filter(is_staff=True)
    u = get_object_or_404(queryset, pk=user.pk)


def add_permissions(permissions_to_add, user):
    for permission in permissions_to_add:
        permission = Permission.objects.get(codename=permission)
        user.user_permissions.add(permission)


def remove_permissions(permissions_to_remove, user):
    for permission in permissions_to_remove:
        permission = Permission.objects.get(codename=permission)
        user.user_permissions.remove(permission)


def build_permission_choices(cls):
    cls = uncamel(cls.__name__).lower()
    choices = []
    for permission in PERMISSIONS_CHOICES:
        choices.append((permission[0] + "_" + cls, permission[1]))
    return tuple(choices)


def uncamel(x):
    final = ''
    for item in x:
        if item.isupper():
            final += "_" + item.lower()
        else:
            final += item
    if final[0] == "_":
        final = final[1:]
    return final
