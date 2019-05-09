from graphene import List, ObjectType

from .sql.types import DjangoDebugSQL


class DjangoDebug(ObjectType):
    sql = List(DjangoDebugSQL)
