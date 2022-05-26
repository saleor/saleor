import graphene

from cloneproduct.grapql.mutation import CloneProduct,AlterOrderLine


class CloneProductMutations(graphene.ObjectType):
    cloneproduct = CloneProduct.Field()
    alteroderline = AlterOrderLine.Field()

