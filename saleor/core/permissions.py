from django.contrib.auth.models import Permission
from django.db.models import Q

from ..settings import GROUP_PERMISSIONS_MODELS


def get_user_groups(user):
    return {'groups': list(user.groups.values_list('name', flat=True))}


def get_permissions():
    app_models_dict = {}
    permissions = Permission.objects.all()

    for app_model in GROUP_PERMISSIONS_MODELS:
        app, model = app_model.split(".")
        app_models_dict.setdefault(app, []).append(model)

    q = Q()

    for app, models in app_models_dict.items():
        q |= Q(content_type__app_label=app, content_type__model__in=models)
        q &= ~Q(content_type__app_label=app, codename__startswith='add_')
        q &= ~Q(content_type__app_label=app, codename__startswith='change_')
        q &= ~Q(content_type__app_label=app, codename__startswith='delete_')

    if q:
        permissions = permissions.filter(q)

    return permissions
