from typing import Optional

import graphene
from django.core.exceptions import ValidationError
from graphql.error import GraphQLError

from ....checkout import models
from ....checkout.error_codes import CheckoutErrorCode
from ....checkout.fetch import fetch_checkout_info, fetch_checkout_lines
from ....checkout.utils import (
    invalidate_checkout_prices,
    remove_promo_code_from_checkout,
    remove_voucher_from_checkout,
)
from ...core.descriptions import ADDED_IN_34, DEPRECATED_IN_3X_INPUT
from ...core.mutations import BaseMutation
from ...core.scalars import UUID
from ...core.types import CheckoutError
from ...core.utils import from_global_id_or_error
from ...core.validators import validate_one_of_args_is_in_mutation
from ...discount.dataloaders import load_discounts
from ...discount.types import Voucher
from ...giftcard.types import GiftCard
from ...plugins.dataloaders import load_plugin_manager
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
        error_type_class = CheckoutError
        error_type_field = "checkout_errors"

    @classmethod
    def perform_mutation(
        cls,
        _root,
        info,
        checkout_id=None,
        token=None,
        id=None,
        promo_code=None,
        promo_code_id=None,
    ):
        validate_one_of_args_is_in_mutation(
            CheckoutErrorCode, "promo_code", promo_code, "promo_code_id", promo_code_id
        )

        object_type, promo_code_pk = cls.clean_promo_code_id(promo_code_id)

        checkout = get_checkout(
            cls,
            info,
            checkout_id=checkout_id,
            token=token,
            id=id,
            error_class=CheckoutErrorCode,
        )

        manager = load_plugin_manager(info.context)
        discounts = load_discounts(info.context)
        checkout_info = fetch_checkout_info(checkout, [], discounts, manager)

        removed = False
        if promo_code:
            removed = remove_promo_code_from_checkout(checkout_info, promo_code)
        else:
            removed = cls.remove_promo_code_by_id(
                info, checkout, object_type, promo_code_pk
            )

        if removed:
            lines, _ = fetch_checkout_lines(checkout)
            invalidate_checkout_prices(
                checkout_info,
                lines,
                manager,
                discounts,
                recalculate_discount=False,
                save=True,
            )
            manager.checkout_updated(checkout)

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
    def remove_promo_code_by_id(
        cls, info, checkout: models.Checkout, object_type: str, promo_code_pk: int
    ) -> bool:
        """Detach promo code from the checkout based on the id.

        Return a boolean value that indicates whether this function changed
        the checkout object which then controls whether hooks such as
        `checkout_updated` are triggered.
        """
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
            if checkout.voucher_code == node.code:
                remove_voucher_from_checkout(checkout)
                return True
        else:
            checkout.gift_cards.remove(promo_code_pk)
            return True

        return False
