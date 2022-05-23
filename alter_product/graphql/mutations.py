import logging

import graphene
from graphene_django import DjangoObjectType
from saleor.product import models
from alter_product.graphql.types import AlternativeProduct
from saleor.graphql.core.mutations import ModelMutation
from .AlterProductError import ALterProductError


class AlterProductInput(graphene.InputObjectType):
    id = graphene.Int()
    sku = graphene.String()


# class AlterProductMutations(ModelMutation):
#     class Arguments:
#         input = AlterProductInput(
#             required=True, description="Fields required."
#         )
#
#     class Meta:
#         description = "Creates new alternative product."
#         model = models.ProductVariant
#         error_type_class = ALterProductError
#         error_type_field = "alternative_product_error"
#
#     @classmethod
#     def get_type_for_model(cls):
#         return AlternativeProduct
#
#     @classmethod
#     def perform_mutation(cls, _root, info, **data):
#         product_variant_original = models.ProductVariant.objects.filter(
#                 id=data['input']['id'])
#
#         product_variant_alter = models.ProductVariant(original_id=product_variant_original.id)
#         product_variant_alter.save()
#         res = super().perform_mutation(_root, info, **data)
#         return res

# class ProductVariantType(DjangoObjectType):
#     class Meta:
#         model = models.ProductVariant
#         fields = "__all__"


# class AlterProductMutations(graphene.Mutation):
#     class Arguments:
#         input = AlterProductInput(
#             required=True, description="Fields required."
#         )
#
#     product_variant = graphene.Field(ProductVariantType)
#
#
#     @staticmethod
#     def mutate(root, info, input=None):
#         product_variant1 = models.ProductVariant.objects.get(pk=input['id'])
#         print(product_variant1)
#         new_product_variant = models.ProductVariant()
#         new_product_variant.save()
#         return AlterProductMutations(product_variant=new_product_variant)
#         # new_product_variant = models.ProductVariant(
#         #     sku=input['input']['sku'],
#         #     original_id=input['input']['id'],
#         #     original_sku=product_variant._meta.get_field('sku')
#         # )

class ALterProductType(DjangoObjectType):
    class Meta:
        model = models.ProductVariant
        fields = "__all__"


class AlterProductMutations(graphene.Mutation):
    class Arguments:
        product_data = AlterProductInput(
            required=True, description="Fields required."
        )

    product = graphene.Field(ALterProductType)

    @staticmethod
    def mutate(root, info, product_data=None):
        get_product_variant = models.ProductVariant.objects.get(id=product_data.id)
        logging.error(get_product_variant)
        product_instance = models.ProductVariant(
            sku=product_data.sku,
            original_sku=product_data.sku,
            original_id=product_data.id
        )
        product_instance.save()
        return AlterProductMutations(product=product_instance)
