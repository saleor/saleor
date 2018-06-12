import graphene
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from graphene import relay

from ...account import models
from ..core.types import CountableDjangoObjectType


class PermissionDisplay(graphene.ObjectType):
    code = graphene.String(description='Internal code for permission.')
    name = graphene.String(
        description='Describe action(s) allowed to do by permission.')

    class Meta:
        description = 'Represents a permission object in a friendly form.'


class Address(CountableDjangoObjectType):
    class Meta:
        exclude_fields = ['user_set', 'user_addresses']
        description = 'Represents user address data.'
        interfaces = [relay.Node]
        model = models.Address


class User(CountableDjangoObjectType):
    permissions = graphene.List(PermissionDisplay)

    class Meta:
        exclude_fields = [
            'date_joined', 'password', 'is_superuser', 'ordernote_set',
            'orderhistoryentry_set', 'last_login']
        description = 'Represents user data.'
        interfaces = [relay.Node]
        model = get_user_model()
        filter_fields = {
            'email': ['exact', 'icontains'],
            'default_shipping_address': ['exact'],
            'is_active': ['exact']}

    def resolve_permissions(self, info, **kwargs):
        if self.is_superuser:
            permissions = Permission.objects.all()
        else:
            permissions = (
                self.user_permissions.all() |
                Permission.objects.filter(group__user=self))
        permissions = permissions.select_related('content_type')
        return [PermissionDisplay(
            code='.'.join([permission.content_type.app_label, permission.codename]),
            name=permission.name) for permission in permissions]
