import graphene

from saleor.product.models import ProductVariant
from saleor.order.models import OrderLine
from .types import CloneProductType, AlterOrderlineType


class InfoInput(graphene.InputObjectType):
    id = graphene.Int()
    sku = graphene.String()

class CloneProduct(graphene.Mutation):
    class Arguments:
        input = InfoInput(required=True)

    cloneproduct = graphene.Field(CloneProductType)

    @staticmethod
    def mutate(_root, info, input=None):
        get_product_variant = ProductVariant.objects.get(id=input.id)
        product_instance = ProductVariant(
            sku=input.sku,
            orgin_variant_id=input.id,
            origin_sku=get_product_variant.sku,
            name=get_product_variant.name,
            product_id=get_product_variant.product_id,
            track_inventory=get_product_variant.track_inventory,
            weight=get_product_variant.weight,
            metadata=get_product_variant.metadata,
            private_metadata=get_product_variant.private_metadata,
            sort_order=get_product_variant.sort_order
        )
        product_instance.save()
        print(info)
        return CloneProduct(cloneproduct=product_instance)

class AlterInput(graphene.InputObjectType):
    orderline_id = graphene.Int()
    variant_id = graphene.Int()

class AlterOrderLine(graphene.Mutation):
    class Arguments:
        alter_input = AlterInput(required=True)

    alter_order_line= graphene.Field(AlterOrderlineType)

    def mutate(_root, info, alter_input=None):
        get_order = OrderLine.Object().get(id=alter_input.id)
        order_line_instance = OrderLine(
            product_sku=input.product_sku,
            original_product_sku=get_order.product_sku,
            variant_id=input.variant_id,
            original_variant_id=get_order.variant_id,
            product_name=get_order.product_name,
            quantity=get_order.quantity,
            unit_price_net_amount=get_order.unit_price_net_amount,
            unit_price_gross_amount=get_order.unit_price_gross_amount,
            order_id=get_order.order_id,
            is_shipping_required=get_order.is_shipping_required,
            total_price_gross_amount=get_order.total_price_gross_amount,
            total_price_net_amount=get_order.total_price_net_amount,
            currency=get_order.currency,
            variant_name=get_order.variant_name
        )
        order_line_instance.save()
        return AlterOrderLine(order_line=order_line_instance)




