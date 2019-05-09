import graphene
from graphene.types.unmountedtype import UnmountedType


class ErrorType(graphene.ObjectType):
    field = graphene.String(required=True)
    messages = graphene.List(graphene.NonNull(graphene.String), required=True)


class DictType(UnmountedType):
    key = graphene.String()
    value = graphene.String()
