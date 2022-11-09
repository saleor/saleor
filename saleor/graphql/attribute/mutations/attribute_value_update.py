import graphene
from django.db import transaction
from django.db.models import Exists, OuterRef, Q, Subquery

from ....attribute import models as models
from ....core.permissions import ProductTypePermissions
from ....product import models as product_models
from ...core.types import AttributeError
from ...plugins.dataloaders import load_plugin_manager
from ..types import Attribute, AttributeValue
from .attribute_update import AttributeValueUpdateInput
from .attribute_value_create import AttributeValueCreate


class AttributeValueUpdate(AttributeValueCreate):
    attribute = graphene.Field(Attribute, description="The updated attribute.")

    class Arguments:
        id = graphene.ID(
            required=True, description="ID of an AttributeValue to update."
        )
        input = AttributeValueUpdateInput(
            required=True, description="Fields required to update an AttributeValue."
        )

    class Meta:
        model = models.AttributeValue
        object_type = AttributeValue
        description = "Updates value of an attribute."
        permissions = (ProductTypePermissions.MANAGE_PRODUCT_TYPES_AND_ATTRIBUTES,)
        error_type_class = AttributeError
        error_type_field = "attribute_errors"

    @classmethod
    def clean_input(cls, info, instance, data):
        cleaned_input = super().clean_input(info, instance, data)
        if cleaned_input.get("value"):
            cleaned_input["file_url"] = ""
            cleaned_input["content_type"] = ""
        elif cleaned_input.get("file_url"):
            cleaned_input["value"] = ""
        return cleaned_input

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        return super(AttributeValueCreate, cls).perform_mutation(_root, info, **data)

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.attribute = instance.attribute
        return response

    @classmethod
    def post_save_action(cls, info, instance, cleaned_input):
        with transaction.atomic():
            variants = product_models.ProductVariant.objects.filter(
                Exists(instance.variantassignments.filter(variant_id=OuterRef("id")))
            )
            # SELECT … FOR UPDATE needs to lock rows in a consistent order
            # to avoid deadlocks between updates touching the same rows.
            qs = (
                product_models.Product.objects.select_for_update(of=("self",))
                .filter(
                    Q(
                        Exists(
                            instance.productassignments.filter(
                                product_id=OuterRef("id")
                            )
                        )
                    )
                    | Q(Exists(variants.filter(product_id=OuterRef("id"))))
                )
                .order_by("pk")
            )
            # qs is executed in a subquery to make sure the SELECT statement gets
            # properly evaluated and locks the rows in the same order every time.
            product_models.Product.objects.filter(
                pk__in=Subquery(qs.values("pk"))
            ).update(search_index_dirty=True)

        manager = load_plugin_manager(info.context)
        cls.call_event(manager.attribute_value_updated, instance)
        cls.call_event(manager.attribute_updated, instance.attribute)
