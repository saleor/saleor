import graphene
from graphene import relay
from graphene_django import DjangoConnectionField, DjangoObjectType

from ...userprofile.models import Address, User
from ..utils import DjangoPkInterface


class AddressType(DjangoObjectType):
    class Meta:
        interfaces = (relay.Node, DjangoPkInterface)
        model = Address
        exclude_fields = ('phone', )


class UserType(DjangoObjectType):
    addresses = DjangoConnectionField(AddressType)

    class Meta:
        interfaces = (relay.Node, DjangoPkInterface)
        model = User
        exclude_fields = ('password', )


def resolve_user(user):
    if user.is_authenticated():
        return user
    return None
