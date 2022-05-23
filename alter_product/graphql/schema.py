import graphene

from .mutations import AlterProductMutations, AlterOrderLineMutations, \
    ALterOrderLineType
from saleor.order.models import OrderLine


class AlternativeProductMutations(graphene.ObjectType):
    alter_product = AlterProductMutations.Field()
    alter_order_line = AlterOrderLineMutations.Field()


class AlternativeOrderQuerries(graphene.ObjectType):
    all_order_lines = graphene.List(ALterOrderLineType)

    # order_lines = graphene.Field(ALterOrderLineType, id=graphene.Int())

    def resolve_all_order_lines(self, info, **kwargs):
        return OrderLine.objects.exclude(original_product_sku__isnull=True,
                                         original_variant_id__isnull=True)
