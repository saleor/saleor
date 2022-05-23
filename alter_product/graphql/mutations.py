import graphene
from graphene_django import DjangoObjectType
from saleor.product.models import ProductVariant
from saleor.order.models import OrderLine


class AlterProductInput(graphene.InputObjectType):
    id = graphene.Int()
    sku = graphene.String()


class ALterProductType(DjangoObjectType):
    class Meta:
        model = ProductVariant
        fields = "__all__"


class AlterProductMutations(graphene.Mutation):
    class Arguments:
        product_input = AlterProductInput(
            required=True, description="Fields required."
        )

    product = graphene.Field(ALterProductType)

    @staticmethod
    def mutate(root, info, product_input=None):
        get_product_variant = ProductVariant.objects.get(id=product_input.id)
        product_instance = ProductVariant(
            sku=product_input.sku,
            original_id=product_input.id,
            original_sku=get_product_variant.sku,
            name=get_product_variant.name,
            product_id=get_product_variant.product_id,
            track_inventory=get_product_variant.track_inventory,
            weight=get_product_variant.weight,
            metadata=get_product_variant.metadata,
            private_metadata=get_product_variant.private_metadata,
            sort_order=get_product_variant.sort_order
        )
        product_instance.save()
        return AlterProductMutations(product=product_instance)


class AlterOrderLineInput(graphene.InputObjectType):
    order_line_id = graphene.Int()
    variant_id = graphene.Int()
    product_sku = graphene.String()


class ALterOrderLineType(DjangoObjectType):
    class Meta:
        model = OrderLine
        fields = "__all__"


class AlterOrderLineMutations(graphene.Mutation):
    class Arguments:
        order_line_input = AlterOrderLineInput(
            required=True, description="Fields required."
        )

    order_line = graphene.Field(ALterOrderLineType)

    @staticmethod
    def mutate(root, info, order_line_input=None):
        get_order = OrderLine.objects.get(id=order_line_input.order_line_id)
        order_line_instance = OrderLine(
            product_sku=order_line_input.product_sku,
            original_product_sku=get_order.product_sku,
            variant_id=order_line_input.variant_id,
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
        return AlterOrderLineMutations(order_line=order_line_instance)

