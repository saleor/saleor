import graphene

from . import fields  # noqa
from .context import SaleorContext

__all__ = ["SaleorContext"]


class ResolveInfo(graphene.ResolveInfo):
    context: SaleorContext
