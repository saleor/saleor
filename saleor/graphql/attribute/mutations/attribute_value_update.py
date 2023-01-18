import graphene
from django.db import transaction
from django.db.models import Exists, OuterRef, Q

from ....attribute import models as models
from ....permission.enums import ProductTypePermissions
from ....product import models as product_models
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_310
from ...core.mutations import ModelWithExtRefMutation
from ...core.types import AttributeError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Attribute, AttributeValue
from .attribute_update import AttributeValueUpdateInput
from .attribute_value_create import AttributeValueCreate

PRODUCTS_BATCH_SIZE = 10000


def queryset_in_batches(queryset):
    """Slice a queryset into batches.

    Input queryset should be sorted be pk.
    """
    start_pk = 0

    while True:
        qs = queryset.filter(pk__gt=start_pk)[:PRODUCTS_BATCH_SIZE]
        pks = list(qs.values_list("pk", flat=True))

        if not pks:
            break

        yield pks

        start_pk = pks[-1]


class AttributeValueUpdate(AttributeValueCreate, ModelWithExtRefMutation):
    attribute = graphene.Field(Attribute, description="The updated attribute.")

    class Arguments:
        id = graphene.ID(
            required=False, description="ID of an AttributeValue to update."
        )
        external_reference = graphene.String(
            required=False,
            description=f"External ID of an AttributeValue to update. {ADDED_IN_310}",
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
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)
        if cleaned_input.get("value"):
            cleaned_input["file_url"] = ""
            cleaned_input["content_type"] = ""
        elif cleaned_input.get("file_url"):
            cleaned_input["value"] = ""
        return cleaned_input

    @classmethod
    def perform_mutation(cls, root, info: ResolveInfo, /, **data):
        return super(AttributeValueCreate, cls).perform_mutation(root, info, **data)

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.attribute = instance.attribute
        return response

    @classmethod
    def post_save_action(cls, info: ResolveInfo, instance, cleaned_input):
        with transaction.atomic():
            variants = product_models.ProductVariant.objects.filter(
                Exists(instance.variantassignments.filter(variant_id=OuterRef("id")))
            )
            # SELECT … FOR UPDATE needs to lock rows in a consistent order
            # to avoid deadlocks between updates touching the same rows.
            qs = (
                product_models.Product.objects.select_for_update(of=("self",))
                .filter(
                    Q(search_index_dirty=False)
                    & (
                        Q(
                            Exists(
                                instance.productassignments.filter(
                                    product_id=OuterRef("id")
                                )
                            )
                        )
                        | Q(Exists(variants.filter(product_id=OuterRef("id"))))
                    )
                )
                .order_by("pk")
            )
            for batch_pks in queryset_in_batches(qs):
                product_models.Product.objects.filter(pk__in=batch_pks).update(
                    search_index_dirty=True
                )

        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.attribute_value_updated, instance)
        cls.call_event(manager.attribute_updated, instance.attribute)
