import graphene
from django.db.models.expressions import Exists, OuterRef

from ....attribute import AttributeInputType
from ....attribute import models as attribute_models
from ....core.tracing import traced_atomic_transaction
from ....page import models
from ....permission.enums import PagePermissions
from ....product.models import Product
from ....product.utils.search_helpers import (
    mark_products_search_vector_as_dirty_in_batches,
)
from ...core import ResolveInfo
from ...core.context import ChannelContext
from ...core.mutations import ModelDeleteMutation
from ...core.types import PageError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Page


class PageDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a page to delete.")

    class Meta:
        description = "Deletes a page."
        model = models.Page
        object_type = Page
        permissions = (PagePermissions.MANAGE_PAGES,)
        error_type_class = PageError
        error_type_field = "page_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        page = cls.get_instance(info, **data)
        manager = get_plugin_manager_promise(info.context).get()
        page_type = page.page_type
        with traced_atomic_transaction():
            cls.delete_assigned_attribute_values(page)
            cls.update_products_search_index(page)
            response = super().perform_mutation(_root, info, **data)
            page.page_type = page_type
            cls.call_event(manager.page_deleted, page)
        response.page = ChannelContext(page, channel_slug=None)
        return response

    @classmethod
    def update_products_search_index(cls, instance):
        # Mark products that use this instance as reference as dirty
        product_ids = list(
            Product.objects.filter(
                Exists(
                    attribute_models.AssignedProductAttributeValue.objects.filter(
                        value__in=attribute_models.AttributeValue.objects.filter(
                            reference_page=instance
                        ),
                        product_id=OuterRef("id"),
                    )
                )
            ).values_list("id", flat=True)
        )
        mark_products_search_vector_as_dirty_in_batches(product_ids)

    @staticmethod
    def delete_assigned_attribute_values(instance):
        assigned_values = attribute_models.AssignedPageAttributeValue.objects.filter(
            page_id=instance.pk
        )
        attributes = attribute_models.Attribute.objects.filter(
            input_type__in=AttributeInputType.TYPES_WITH_UNIQUE_VALUES
        )

        attribute_models.AttributeValue.objects.filter(
            Exists(assigned_values.filter(value_id=OuterRef("id"))),
            Exists(attributes.filter(id=OuterRef("attribute_id"))),
        ).delete()
