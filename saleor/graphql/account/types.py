import graphene
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from graphene import relay

from ..core.types import CountableDjangoObjectType


class User(CountableDjangoObjectType):

    permissions = graphene.List(graphene.String)

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
            return Permission.objects.all()
        return self.user_permissions.all() | Permission.objects.filter(
            group__user=self)
