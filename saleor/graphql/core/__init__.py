import graphene

from . import fields  # noqa: F401
from .context import SaleorContext

__all__ = ["SaleorContext"]


class ResolveInfo(graphene.ResolveInfo):
    context: SaleorContext
