from typing import Optional

import graphene
from django.core.exceptions import ValidationError
from graphql.error import GraphQLError

from ....checkout import models
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.utils import (
    invalidate_checkout,
    remove_promo_code_from_checkout_or_error,
    remove_voucher_from_checkout,
)
from ....webhook.event_types import WebhookEventAsyncType
from ...core import ResolveInfo
from ...core.descriptions import ADDED_IN_34, DEPRECATED_IN_3X_INPUT
from ...core.doc_category import DOC_CATEGORY_CHECKOUT
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError
from ...core.utils import WebhookEventInfo, from_global_id_or_error
from ...core.validators import validate_one_of_args_is_in_mutation
from ...discount.types import Voucher
from ...giftcard.types import GiftCard
from ...plugins.dataloaders import get_plugin_manager_promise
from ..types import Checkout
from .utils import get_checkout


class CheckoutRemovePromoCode(BaseMutation):
    checkout = graphene.Field(
        Checkout, description="The checkout with the removed gift card or voucher."
    )

    class Arguments:
        id = graphene.ID(
            description="The checkout's ID." + ADDED_IN_34,
            required=False,
        )
        token = UUID(
            description=f"Checkout token.{DEPRECATED_IN_3X_INPUT} Use `id` instead.",
            required=False,
        )
        checkout_id = graphene.ID(
            required=False,
            description=(
                f"The ID of the checkout. {DEPRECATED_IN_3X_INPUT} Use `id` instead."
            ),
        )
        promo_code = graphene.String(
            description="Gift card code or voucher code.", required=False
        )
        promo_code_id = graphene.ID(
            description="Gift card or voucher ID.",
            required=False,
        )

    class Meta:
        description = "Remove a gift card or a voucher from a checkout."
        doc_category = DOC_CATEGORY_CHECKOUT
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.CHECKOUT_UPDATED,
                description="A checkout was updated.",
            )
        ]

    @classmethod
    def perform_mutation(
        cls,
        _root,
        info,
        /,
        checkout_id=None,
        token=None,
        id=None,
        promo_code=None,
        promo_code_id=None,
    ):
        validate_one_of_args_is_in_mutation(
            "promo_code", promo_code, "promo_code_id", promo_code_id
        )

        checkout = get_checkout(cls, info, checkout_id=checkout_id, token=token, id=id)

        manager = get_plugin_manager_promise(info.context).get()
        checkout_info = fetch_checkout_info(checkout, [], manager)

        if promo_code:
            try:
                remove_promo_code_from_checkout_or_error(checkout_info, promo_code)
            except ValidationError as error:
                raise ValidationError({"promo_code": error})
        else:
            object_type, promo_code_pk = cls.clean_promo_code_id(promo_code_id)
            cls.remove_promo_code_by_id_or_error(
                info, checkout, object_type, promo_code_pk
            )
        # if this step is reached, it means promo code was removed
        lines, _ = fetch_checkout_lines(checkout)
        invalidate_checkout(
            checkout_info,
            lines,
            manager,
            recalculate_discount=True,
            save=True,
        )
        cls.call_event(manager.checkout_updated, checkout)

        return CheckoutRemovePromoCode(checkout=checkout)

    @staticmethod
    def clean_promo_code_id(promo_code_id: Optional[str]):
        if promo_code_id is None:
            return None, None
        try:
            object_type, promo_code_pk = from_global_id_or_error(
                promo_code_id, raise_error=True
            )
        except GraphQLError as e:
            raise ValidationError(
                {
                    "promo_code_id": ValidationError(
                        str(e), code=CheckoutErrorCode.GRAPHQL_ERROR.value
                    )
                }
            )

        if object_type not in (str(Voucher), str(GiftCard)):
            raise ValidationError(
                {
                    "promo_code_id": ValidationError(
                        "Must receive Voucher or GiftCard id.",
                        code=CheckoutErrorCode.NOT_FOUND.value,
                    )
                }
            )

        return object_type, promo_code_pk

    @classmethod
    def remove_promo_code_by_id_or_error(
        cls,
        info: ResolveInfo,
        checkout: models.Checkout,
        object_type: str,
        promo_code_pk: int,
    ) -> None:
        """Detach promo code from the checkout based on the id or raise an error."""
        if object_type == str(Voucher) and checkout.voucher_code is not None:
            node = cls._get_node_by_pk(info, graphene_type=Voucher, pk=promo_code_pk)
            if node is None:
                raise ValidationError(
                    {
                        "promo_code_id": ValidationError(
                            f"Couldn't resolve to a node: {promo_code_pk}",
                            code=CheckoutErrorCode.NOT_FOUND.value,
                        )
                    }
                )
            if checkout.voucher_code in node.promo_codes:
                remove_voucher_from_checkout(checkout)
            else:
                raise ValidationError(
                    {
                        "promo_code_id": ValidationError(
                            "Couldn't remove a promo code from a checkout.",
                            code=CheckoutErrorCode.NOT_FOUND.value,
                        )
                    }
                )
        else:
            checkout.gift_cards.remove(promo_code_pk)
