import graphene
from django.db.models import Q
from django.db.models.expressions import Exists, OuterRef

from .....attribute import AttributeInputType
from .....attribute import models as attribute_models
from .....core.tracing import traced_atomic_transaction
from .....order import OrderStatus
from .....order import models as order_models
from .....permission.enums import ProductTypePermissions
from .....product import models
from ....core import ResolveInfo
from ....core.doc_category import DOC_CATEGORY_PRODUCTS
from ....core.mutations import ModelDeleteMutation
from ....core.types import ProductError
from ...types import ProductType


class ProductTypeDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a product type to delete.")

    class Meta:
        description = "Deletes a product type."
        doc_category = DOC_CATEGORY_PRODUCTS
        model = models.ProductType
        object_type = ProductType
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    @traced_atomic_transaction()
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str
    ):
        product_type_pk = cls.get_global_id_or_error(
            id, only_type=ProductType, field="pk"
        )
        variants_pks = models.Product.objects.filter(
            product_type__pk=product_type_pk
        ).values_list("variants__pk", flat=True)
        # get draft order lines for products
        order_line_pks = list(
            order_models.OrderLine.objects.filter(
                variant__pk__in=variants_pks, order__status=OrderStatus.DRAFT
            ).values_list("pk", flat=True)
        )
        cls.delete_assigned_attribute_values(product_type_pk)

        response = super().perform_mutation(_root, info, id=id)

        # delete order lines for deleted variants
        order_models.OrderLine.objects.filter(pk__in=order_line_pks).delete()

        return response

    @staticmethod
    def delete_assigned_attribute_values(instance_pk):
        attributes = attribute_models.Attribute.objects.filter(
            input_type__in=AttributeInputType.TYPES_WITH_UNIQUE_VALUES
        )
        assigned_values = attribute_models.AssignedProductAttributeValue.objects.filter(
            product__product_type_id=instance_pk
        )
        attribute_models.AttributeValue.objects.filter(
            Exists(attributes.filter(id=OuterRef("attribute_id"))),
            (
                Q(Exists(assigned_values.filter(value_id=OuterRef("id"))))
                | Q(variantassignments__assignment__product_type_id=instance_pk)
            ),
        ).delete()
