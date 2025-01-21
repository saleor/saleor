from .....core.tracing import traced_atomic_transaction
from .....discount.error_codes import DiscountErrorCode
from .....discount.models import Promotion, PromotionRule
from .....permission.enums import DiscountPermissions
from .....webhook.event_types import WebhookEventAsyncType
from ....channel import ChannelContext
from ....core import ResolveInfo
from ....core.descriptions import DEPRECATED_IN_3X_MUTATION
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.types import DiscountError
from ....core.utils import (
    WebhookEventInfo,
    from_global_id_or_error,
    raise_validation_error,
)
from ...utils import (
    CatalogueInfo,
    convert_catalogue_info_into_predicate,
    convert_migrated_sale_predicate_to_catalogue_info,
    merge_catalogues_info,
)
from .sale_base_catalogue import SaleBaseCatalogueMutation


class SaleAddCatalogues(SaleBaseCatalogueMutation):
    class Meta:
        description = (
            "Adds products, categories, collections to a sale."
            + DEPRECATED_IN_3X_MUTATION
            + " Use `promotionRuleCreate` mutation instead."
        )
        doc_category = DOC_CATEGORY_DISCOUNTS
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = DiscountError
        error_type_field = "discount_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.SALE_UPDATED,
                description="A sale was updated.",
            ),
        ]

    @classmethod
    def perform_mutation(  # type: ignore[override]
        cls, _root, info: ResolveInfo, /, *, id: str, input
    ):
        promotion = cls.get_instance(info, id)
        rules = promotion.rules.all()
        previous_predicate = rules[0].catalogue_predicate
        previous_catalogue_info = convert_migrated_sale_predicate_to_catalogue_info(
            previous_predicate
        )

        with traced_atomic_transaction():
            new_catalogue_info = cls.add_items_to_catalogue(
                rules, previous_catalogue_info, input
            )
            cls.post_save_actions(
                info,
                promotion,
                previous_catalogue_info,
                new_catalogue_info,
            )

        return SaleAddCatalogues(sale=ChannelContext(node=promotion, channel_slug=None))

    @classmethod
    def get_instance(cls, _info: ResolveInfo, id):
        type, _id = from_global_id_or_error(id, raise_error=False)
        if type == "Promotion":
            raise_validation_error(
                field="id",
                message="Provided ID refers to Promotion model. "
                "Please use 'promotionRuleCreate' mutation instead.",
                code=DiscountErrorCode.INVALID.value,
            )
        object_id = cls.get_global_id_or_error(id, "Sale")
        try:
            return Promotion.objects.get(old_sale_id=object_id)
        except Promotion.DoesNotExist:
            raise_validation_error(
                field="id",
                message="Sale with given ID can't be found.",
                code=DiscountErrorCode.NOT_FOUND,
            )

    @classmethod
    def add_items_to_catalogue(
        cls, rules: list[PromotionRule], previous_catalogue_info: CatalogueInfo, input
    ) -> dict | None:
        catalogue_info_to_add = cls.get_catalogue_info_from_input(input)
        if any(catalogue_info_to_add):
            new_catalogue = merge_catalogues_info(
                previous_catalogue_info, catalogue_info_to_add
            )
            new_predicate = convert_catalogue_info_into_predicate(new_catalogue)
            for rule in rules:
                rule.catalogue_predicate = new_predicate
            PromotionRule.objects.bulk_update(rules, ["catalogue_predicate"])
            return new_catalogue

        return previous_catalogue_info
