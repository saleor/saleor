import graphene
from saleor.warehouse import models
from saleor.graphql.core.mutations import ModelMutation
from .. import models
from ..error_codes import TransferStockError
from saleor.warehouse.models import Stock


def check_stock_product_variant_available(source, quantity_requested, product_variant):
    warehouse_stock_source = Stock.objects.filter(warehouse=source,
                                            product_variant=product_variant).first()
    if warehouse_stock_source.annotate_available_quantity() < quantity_requested:
        raise TransferStockError


class CreateTransferStockInput(graphene.InputObjectType):
    source_warehouse = graphene.ID(
        required=True,
        description="Warehouse send product"
    )
    next_warehouse = graphene.ID(
        required=True,
        description="Warehouse recipe product")
    product_variant = graphene.ID(
        required=True,
        description="Product variant sent"
    )
    quantity_request = graphene.Int(
        required=True,
        description="Quantity of product sent"
    )


class CreateTransferStock(ModelMutation):
    created = graphene.Field(
        graphene.Boolean,
        description=(
            "Whether the checkout was created or the current active one was returned. "
            "Refer to checkoutLinesAdd and checkoutLinesUpdate to merge a cart "
            "with an active checkout."
            "DEPRECATED: Will be removed in Saleor 4.0. Always returns True."
        ),
    )

    class Arguments:
        input = CreateTransferStockInput(
            required=True, description="Fields required to create transfer stock."
        )

    class Meta:
        description = "Creates new transfer stock."
        model = models.StockNotify
        # permissions = (ProductPermissions.MANAGE_PRODUCTS,)
        error_type_class = TransferStockError
        error_type_field = "transfer_stock_error"

    @classmethod
    # @traced_atomic_transaction()
    def save(cls, info, instance, cleaned_input):

        # Create the checkout object
        instance.save()

    @classmethod
    def get_instance(cls, info, **data):
        instance = super().get_instance(info, **data)
        user = info.context.user
        if user.is_authenticated:
            instance.user = user
        return instance

    @classmethod
    def clean_input(cls, info, instance, data, input_cls=None):
        user = info.context.user

        pass

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        # source_warehouse = data.get("source_warehouse")
        # next_warehouse = data.get("next_warehouse")
        # super(cls, CreateTransferStock).perform_mutation()
        res = super().perform_mutation(_root, info, **data)
        return res


