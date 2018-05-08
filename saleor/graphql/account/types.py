import graphene
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from graphene import relay

from ..core.types import CountableDjangoObjectType


class PermissionDisplay(graphene.ObjectType):
    code = graphene.String(description="Internal code for permission.")
    name = graphene.String(description=
                           "Describe action(s) allowed to do by permission.")

    class Meta:
        description = 'Represents a permission object in a friendly form.'


class User(CountableDjangoObjectType):

    permissions = graphene.List(PermissionDisplay)

    class Meta:
        exclude_fields = [
            'addresses', 'is_staff', 'is_active', 'date_joined', 'password',
            'default_shipping_address', 'default_billing_address',
            'is_superuser', 'last_login']
        description = "Represents user data."
        interfaces = [relay.Node]
        model = get_user_model()

    def resolve_permissions(self, info, **kwargs):
        if self.is_superuser:
            permissions = Permission.objects.all().select_related(
                'content_type')
        else:
            permissions = (
                self.user_permissions.all() | Permission.objects.filter(
            group__user=self)).select_related('content_type')
        return [PermissionDisplay(
            code='.'.join([permission.content_type.app_label, permission.codename]),
            name=permission.name) for permission in permissions]
