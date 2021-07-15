import graphene
from django.core.exceptions import ValidationError
from django.utils import timezone

from ....core.permissions import OrderPermissions
from ....order import SubscriptionStatus
from ....order.actions import (
    subscription_cancel,
    subscription_renew,
    subscription_update_status,
)
from ....order.error_codes import SubscriptionErrorCode
from ...core.enums import SubscriptionStatusEnum
from ...core.mutations import BaseMutation
from ...core.types.common import SubscriptionError
from ...order.types import Subscription


class SubscriptionRenew(BaseMutation):
    subscription = graphene.Field(Subscription, description="Renewed subscription.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the subscription to renew.")

    class Meta:
        description = "Renew a subscription."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = SubscriptionError
        error_type_field = "subscription_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        subscription = cls.get_node_or_error(
            info, data.get("id"), only_type=Subscription
        )
        if subscription.can_renew():
            subscription_renew(subscription=subscription)
        else:
            if subscription.status not in [
                SubscriptionStatus.PENDING,
                SubscriptionStatus.ACTIVE,
                SubscriptionStatus.ON_HOLD,
            ]:
                raise ValidationError(
                    {
                        "status": ValidationError(
                            "Provided subscription with status cannot renew. ",
                            code=SubscriptionErrorCode.CANNOT_RENEW,
                        )
                    }
                )
            elif subscription.expiry_date and subscription.expiry_date < timezone.now():
                raise ValidationError(
                    {
                        "expiry_date": ValidationError(
                            "Provided subscription already expired. ",
                            code=SubscriptionErrorCode.CANNOT_RENEW,
                        )
                    }
                )
            elif subscription.next_payment_date > timezone.now():
                raise ValidationError(
                    {
                        "next_payment_date": ValidationError(
                            "Provided subscription cannot renew before "
                            "next payment data.",
                            code=SubscriptionErrorCode.CANNOT_RENEW,
                        )
                    }
                )

        return SubscriptionRenew(subscription=subscription)


class SubscriptionUpdateStatus(BaseMutation):
    subscription = graphene.Field(
        Subscription, description="Update subscription status."
    )

    class Arguments:
        id = graphene.ID(
            description="ID of the subscription to update status.", required=True
        )
        status = SubscriptionStatusEnum(description="Status to update.", required=True)

    class Meta:
        description = "Update subscription status."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = SubscriptionError
        error_type_field = "subscription_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        subscription = cls.get_node_or_error(
            info, data.get("id"), only_type=Subscription
        )
        status = data.get("status")
        if subscription.can_update_status(status=status):
            subscription_update_status(subscription, status)
        else:
            if status == SubscriptionStatus.PENDING and not (
                subscription.status
                in [SubscriptionStatus.ACTIVE, SubscriptionStatus.ON_HOLD]
                and subscription.end_date <= timezone.now()
            ):
                raise ValidationError(
                    {
                        "status": ValidationError(
                            "Provided subscription cannot update to pending status. ",
                            code=SubscriptionErrorCode.CANNOT_UPDATE_STATUS,
                        )
                    }
                )

            elif status == SubscriptionStatus.ACTIVE and not (
                subscription.status
                in [SubscriptionStatus.PENDING, SubscriptionStatus.ON_HOLD]
            ):
                raise ValidationError(
                    {
                        "status": ValidationError(
                            "Provided subscription cannot update to active status. ",
                            code=SubscriptionErrorCode.CANNOT_UPDATE_STATUS,
                        )
                    }
                )

            elif status == SubscriptionStatus.ON_HOLD and not (
                subscription.status in [SubscriptionStatus.ACTIVE]
            ):
                raise ValidationError(
                    {
                        "status": ValidationError(
                            "Provided subscription cannot update to on_hold status. ",
                            code=SubscriptionErrorCode.CANNOT_UPDATE_STATUS,
                        )
                    }
                )

        return SubscriptionUpdateStatus(subscription=subscription)


class SubscriptionCancel(BaseMutation):
    subscription = graphene.Field(Subscription, description="Canceled subscription.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the subscription to cancel.")

    class Meta:
        description = "Cancel a subscription."
        permissions = (OrderPermissions.MANAGE_ORDERS,)
        error_type_class = SubscriptionError
        error_type_field = "subscription_errors"

    @classmethod
    def perform_mutation(cls, _root, info, **data):
        subscription = cls.get_node_or_error(
            info, data.get("id"), only_type=Subscription
        )
        subscription_cancel(subscription=subscription)

        return SubscriptionCancel(subscription=subscription)
