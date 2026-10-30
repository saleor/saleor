import graphene
from django.core.exceptions import ValidationError

from .....core.tracing import traced_atomic_transaction
from .....discount.error_codes import DiscountErrorCode
from .....discount.interface import fetch_voucher_catalogue_pks
from .....discount.lock_objects import voucher_qs_select_for_update
from .....permission.enums import DiscountPermissions
from .....product.utils import get_products_ids_without_variants
from .....webhook.event_types import WebhookEventAsyncType
from ....core import ResolveInfo
from ....core.context import ChannelContext
from ....core.descriptions import ADDED_IN_323, DEPRECATED_IN_3X_INPUT
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.mutations import BaseMutation
from ....core.types import BaseInputObjectType, DiscountError, NonNullList
from ....core.utils import WebhookEventInfo
from ....core.validators import validate_one_of_args_is_in_mutation
from ....plugins.dataloaders import get_plugin_manager_promise
from ...types import Voucher
from .catalogue_validation import (
    EXCLUSION_DESCRIPTION,
    VOUCHER_CATALOGUE_ITEMS_LIMIT,
    VOUCHER_CATALOGUE_NODE_TYPES,
    clean_voucher_catalogue,
    resolve_voucher_catalogue_nodes,
    validate_voucher_catalogue_items_limit,
)

INCLUDE_DESCRIPTION = (
    "{entity} related to the voucher. "
    f"Max {VOUCHER_CATALOGUE_ITEMS_LIMIT} items per call."
)


class CatalogueInput(BaseInputObjectType):
    products = NonNullList(
        graphene.ID, description="Products related to the discount.", name="products"
    )
    categories = NonNullList(
        graphene.ID,
        description="Categories related to the discount.",
        name="categories",
    )
    collections = NonNullList(
        graphene.ID,
        description="Collections related to the discount.",
        name="collections",
    )
    variants = NonNullList(
        graphene.ID,
        description="Product variant related to the discount.",
        name="variants",
    )

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS


class VoucherCatalogueInput(BaseInputObjectType):
    products = NonNullList(
        graphene.ID, description=INCLUDE_DESCRIPTION.format(entity="Products")
    )
    categories = NonNullList(
        graphene.ID, description=INCLUDE_DESCRIPTION.format(entity="Categories")
    )
    collections = NonNullList(
        graphene.ID, description=INCLUDE_DESCRIPTION.format(entity="Collections")
    )
    variants = NonNullList(
        graphene.ID, description=INCLUDE_DESCRIPTION.format(entity="Product variants")
    )
    product_types = NonNullList(
        graphene.ID, description=INCLUDE_DESCRIPTION.format(entity="Product types")
    )
    excluded_products = NonNullList(
        graphene.ID,
        description=EXCLUSION_DESCRIPTION.format(entity="Products"),
    )
    excluded_categories = NonNullList(
        graphene.ID,
        description=EXCLUSION_DESCRIPTION.format(entity="Categories"),
    )
    excluded_collections = NonNullList(
        graphene.ID,
        description=EXCLUSION_DESCRIPTION.format(entity="Collections"),
    )
    excluded_variants = NonNullList(
        graphene.ID,
        description=EXCLUSION_DESCRIPTION.format(entity="Product variants"),
    )
    excluded_product_types = NonNullList(
        graphene.ID,
        description=EXCLUSION_DESCRIPTION.format(entity="Product types"),
    )

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS
        description = (
            "Catalogue items a voucher includes or excludes. An item matched by "
            "any exclusion is never discounted by the voucher." + ADDED_IN_323
        )


class VoucherBaseCatalogueMutation(BaseMutation):
    voucher = graphene.Field(
        Voucher, description="Voucher of which catalogue IDs will be modified."
    )

    class Arguments:
        id = graphene.ID(required=True, description="ID of a voucher.")
        input = CatalogueInput(
            description=(
                "Fields required to modify catalogue IDs of voucher. "
                "Cannot be combined with `catalogue`."
                + DEPRECATED_IN_3X_INPUT
                + " Use `catalogue` instead."
            ),
        )
        catalogue = VoucherCatalogueInput(
            description=(
                "Catalogue IDs of the voucher to modify. "
                "Cannot be combined with `input`." + ADDED_IN_323
            ),
        )

    class Meta:
        abstract = True

    @classmethod
    def mutate(cls, root, info: ResolveInfo, **data):
        response = super().mutate(root, info, **data)
        if response.voucher:
            response.voucher = ChannelContext(node=response.voucher, channel_slug=None)
        return response

    @classmethod
    def get_catalogue_nodes(cls, data) -> dict[str, list]:
        """Return catalogue nodes to modify, keyed by Voucher M2M field name."""
        validate_one_of_args_is_in_mutation(
            "input",
            data.get("input") is not None,
            "catalogue",
            data.get("catalogue") is not None,
        )
        if data.get("catalogue") is not None:
            catalogue_input = data["catalogue"]
            validate_voucher_catalogue_items_limit(
                catalogue_input, VOUCHER_CATALOGUE_NODE_TYPES
            )
        else:
            # The deprecated input keeps its include lists uncapped.
            catalogue_input = data["input"]
        return resolve_voucher_catalogue_nodes(catalogue_input)

    @classmethod
    def clean_product(cls, products):
        products_ids_without_variants = get_products_ids_without_variants(products)
        if products_ids_without_variants:
            error_code = DiscountErrorCode.CANNOT_MANAGE_PRODUCT_WITHOUT_VARIANT.value
            raise ValidationError(
                {
                    "products": ValidationError(
                        "Cannot manage products without variants.",
                        code=error_code,
                        params={"products": products_ids_without_variants},
                    )
                }
            )


class VoucherAddCatalogues(VoucherBaseCatalogueMutation):
    class Meta:
        description = "Adds products, categories, collections to a voucher."
        doc_category = DOC_CATEGORY_DISCOUNTS
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.VOUCHER_UPDATED,
                description="A voucher was updated.",
            )
        ]

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        voucher = cls.get_node_or_error(
            info, data["id"], only_type=Voucher, field="voucher_id"
        )
        nodes_by_field = cls.get_catalogue_nodes(data)
        if products := nodes_by_field.get("products"):
            cls.clean_product(products)
        input_pks = {
            field: {node.pk for node in nodes}
            for field, nodes in nodes_by_field.items()
        }
        with traced_atomic_transaction():
            # Lock so a concurrent type change or catalogue edit can't slip past
            # the validation below.
            voucher = voucher_qs_select_for_update().get(pk=voucher.pk)
            stored_pks = fetch_voucher_catalogue_pks(voucher)
            clean_voucher_catalogue(
                voucher.type,
                {
                    field: stored_pks.get(field, set()) | input_pks.get(field, set())
                    for field in VOUCHER_CATALOGUE_NODE_TYPES
                },
                input_pks,
            )
            for field, nodes in nodes_by_field.items():
                getattr(voucher, field).add(*nodes)

            if nodes_by_field:
                manager = get_plugin_manager_promise(info.context).get()
                cls.call_event(manager.voucher_updated, voucher, voucher.code)

        return VoucherAddCatalogues(voucher=voucher)
