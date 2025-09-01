import graphene
from django.db import transaction
from django.db.models import Exists, OuterRef

from ....attribute import models as attribute_models
from ....core.utils.update_mutation_manager import InstanceTracker
from ....page import models
from ....permission.enums import PagePermissions
from ....product.lock_objects import product_qs_select_for_update
from ....product.models import Product
from ...attribute.utils.attribute_assignment import AttributeAssignmentMixin
from ...core import ResolveInfo
from ...core.context import ChannelContext
from ...core.types import PageError
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Page
from .page_create import PageCreate, PageInput


class PageUpdate(PageCreate):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a page to update.")
        input = PageInput(
            required=True, description="Fields required to update a page."
        )

    class Meta:
        description = "Updates an existing page."
        model = models.Page
        object_type = Page
        permissions = (PagePermissions.MANAGE_PAGES,)
        error_type_class = PageError
        error_type_field = "page_errors"
        instance_tracker_fields = [
            "title",
        ]

    @classmethod
    def clean_attributes(cls, attributes: list[dict], page_type: models.PageType):
        attributes_qs = page_type.page_attributes.prefetch_related("values")
        cleaned_attributes = AttributeAssignmentMixin.clean_input(
            attributes, attributes_qs, creation=False, is_page_attributes=True
        )
        return cleaned_attributes

    @classmethod
    def save(
        cls,
        info: ResolveInfo,
        instance,
        cleaned_input,
        instance_tracker: InstanceTracker | None = None,
    ):
        super(PageCreate, cls).save(info, instance, cleaned_input)
        manager = get_plugin_manager_promise(info.context).get()
        cls.call_event(manager.page_updated, instance)

        if instance_tracker is not None:
            modified_instance_fields = instance_tracker.get_modified_fields()
            if "title" in modified_instance_fields:
                cls.update_products_search_index(instance)

    @classmethod
    def update_products_search_index(cls, instance):
        # Mark products that use this instance as reference as dirty
        with transaction.atomic():
            locked_ids = (
                product_qs_select_for_update()
                .filter(
                    Exists(
                        attribute_models.AssignedProductAttributeValue.objects.filter(
                            value__in=attribute_models.AttributeValue.objects.filter(
                                reference_page=instance
                            ),
                            product_id=OuterRef("id"),
                        )
                    )
                )
                .values_list("id", flat=True)
            )
            Product.objects.filter(id__in=locked_ids).update(search_index_dirty=True)

    @classmethod
    def success_response(cls, instance):
        response = super().success_response(instance)
        response.page = ChannelContext(instance, channel_slug=None)
        return response
