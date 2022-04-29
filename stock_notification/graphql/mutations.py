import graphene
from saleor.warehouse import models
from saleor.graphql.warehouse.mutations import WarehouseMixin
from saleor.graphql.core.mutations import ModelDeleteMutation, ModelMutation
from .. import models
from ..error_codes import TransferStockError
from saleor.warehouse.models import Stock


def check_stock_product_variant_available(source, quantity, product_variant):
    source_warehouse = Stock.objects.filter(warehouse=source,
                                            product_variant=product_variant).first()
    if source_warehouse.quatity - source_warehouse.quatity_allocated < quantity:
        raise TransferStockError


class CreateTransferStockInput(graphene.InputObjectType):
    source_warehouse = graphene.ID()
    next_warehouse = graphene.ID()
    product_variant = graphene.String()
    quantity_request = graphene.Int()


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
        super(CreateTransferStock, self).perform_mutation()


