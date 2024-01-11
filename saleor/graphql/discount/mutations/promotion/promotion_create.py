from collections import defaultdict
from datetime import datetime

import graphene
import pytz
from django.core.exceptions import ValidationError
from django.db import transaction
from graphql.error import GraphQLError

from .....channel import models as channel_models
from .....discount import events, models
from .....permission.enums import DiscountPermissions
from .....plugins.manager import PluginsManager
from .....webhook.event_types import WebhookEventAsyncType
from ....app.dataloaders import get_app_promise
from ....channel.types import Channel
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_317, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.mutations import ModelMutation
from ....core.scalars import JSON
from ....core.types import BaseInputObjectType, Error, NonNullList
from ....core.utils import WebhookEventInfo
from ....core.validators import validate_end_is_after_start
from ....plugins.dataloaders import get_plugin_manager_promise
from ....utils import get_nodes
from ...enums import PromotionCreateErrorCode
from ...inputs import PromotionRuleBaseInput
from ...types import Promotion
from .validators import clean_promotion_rule


class PromotionCreateError(Error):
    code = PromotionCreateErrorCode(description="The error code.", required=True)
    index = graphene.Int(
        description="Index of an input list item that caused the error."
    )


class PromotionRuleInput(PromotionRuleBaseInput):
    channels = NonNullList(
        graphene.ID,
        description="List of channel ids to which the rule should apply to.",
    )

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS


class PromotionInput(BaseInputObjectType):
    description = JSON(description="Promotion description.")
    start_date = graphene.types.datetime.DateTime(
        description="The start date of the promotion in ISO 8601 format."
    )
    end_date = graphene.types.datetime.DateTime(
        description="The end date of the promotion in ISO 8601 format."
    )


class PromotionCreateInput(PromotionInput):
    name = graphene.String(description="Promotion name.", required=True)
    rules = NonNullList(PromotionRuleInput, description="List of promotion rules.")

    class Meta:
        doc_category = DOC_CATEGORY_DISCOUNTS


class PromotionCreate(ModelMutation):
    class Arguments:
        input = PromotionCreateInput(
            description="Fields requires to create a promotion.", required=True
        )

    class Meta:
        description = "Creates a new promotion." + ADDED_IN_317 + PREVIEW_FEATURE
        model = models.Promotion
        object_type = Promotion
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = PromotionCreateError
        doc_category = DOC_CATEGORY_DISCOUNTS
        webhook_events_info = [
            WebhookEventInfo(
                type=WebhookEventAsyncType.PROMOTION_CREATED,
                description="A promotion was created.",
            ),
            WebhookEventInfo(
                type=WebhookEventAsyncType.PROMOTION_STARTED,
                description="Optionally called if promotion was started.",
            ),
        ]

    @classmethod
    def clean_input(
        cls, info: ResolveInfo, instance: models.Promotion, data: dict, **kwargs
    ):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)

        errors: defaultdict[str, list[ValidationError]] = defaultdict(list)
        start_date = cleaned_input.get("start_date") or instance.start_date
        end_date = cleaned_input.get("end_date")
        try:
            validate_end_is_after_start(start_date, end_date)
        except ValidationError as error:
            error.code = PromotionCreateErrorCode.INVALID.value
            errors["end_date"].append(error)

        if rules := cleaned_input.get("rules"):
            cleaned_rules, errors = cls.clean_rules(info, rules, errors)
            cleaned_input["rules"] = cleaned_rules

        if errors:
            raise ValidationError(errors)

        return cleaned_input

    @classmethod
    def clean_rules(
        cls,
        info: ResolveInfo,
        rules_data: dict,
        errors: defaultdict[str, list[ValidationError]],
    ) -> tuple[list, defaultdict[str, list[ValidationError]]]:
        cleaned_rules = []
        for index, rule_data in enumerate(rules_data):
            if channel_ids := rule_data.get("channels"):
                channels = cls.clean_channels(info, channel_ids, index, errors)
                rule_data["channels"] = channels
            clean_promotion_rule(rule_data, errors, PromotionCreateErrorCode, index)
            cleaned_rules.append(rule_data)

        return cleaned_rules, errors

    @classmethod
    def clean_channels(
        cls,
        info: ResolveInfo,
        channel_ids: list[str],
        index: int,
        errors: defaultdict[str, list[ValidationError]],
    ) -> list[channel_models.Channel]:
        try:
            channels = get_nodes(channel_ids, Channel, schema=info.schema)
        except GraphQLError as e:
            errors["channels"].append(
                ValidationError(
                    str(e),
                    code=PromotionCreateErrorCode.GRAPHQL_ERROR.value,
                    params={"index": index},
                )
            )
            return []
        return channels

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, **data):
        instance = cls.get_instance(info, **data)
        data = data["input"]
        cleaned_input = cls.clean_input(info, instance, data)
        instance = cls.construct_instance(instance, cleaned_input)
        cls.clean_instance(info, instance)
        with transaction.atomic():
            cls.save(info, instance, cleaned_input)
            rules = cls._save_m2m(info, instance, cleaned_input)
            cls.post_save_actions(info, instance, rules)

        return cls.success_response(instance)

    @classmethod
    def _save_m2m(
        cls, info: ResolveInfo, instance: models.Promotion, cleaned_data: dict
    ):
        super()._save_m2m(info, instance, cleaned_data)
        rules_with_channels_to_add = []
        rules = []
        if rules_data := cleaned_data.get("rules"):
            for rule_data in rules_data:
                channels = rule_data.pop("channels", None)
                rule = models.PromotionRule(
                    promotion=instance, variants_dirty=True, **rule_data
                )
                rules_with_channels_to_add.append((rule, channels))
                rules.append(rule)
            models.PromotionRule.objects.bulk_create(rules)

        for rule, channels in rules_with_channels_to_add:
            if channels:
                rule.channels.set(channels)

        return rules

    @classmethod
    def post_save_actions(
        cls,
        info,
        instance: models.Promotion,
        rules: list[models.PromotionRule],
    ):
        manager = get_plugin_manager_promise(info.context).get()
        has_started = cls.has_started(instance)
        cls.save_promotion_events(info, instance, rules, has_started)
        cls.call_event(manager.promotion_created, instance)
        if has_started:
            cls.send_promotion_started_webhook(manager, instance)

    @classmethod
    def has_started(cls, instance: models.Promotion) -> bool:
        """Check if promotion has started.

        Return true, when the start date is before the current date and the
        promotion is not already finished.
        """
        now = datetime.now(pytz.utc)
        start_date = instance.start_date
        end_date = instance.end_date

        return (start_date and (start_date <= now)) and (  # type: ignore[return-value] # mypy's return value is type of Union[datetime, bool]  # noqa: E501
            not end_date or not (end_date <= now)
        )

    @classmethod
    def save_promotion_events(
        cls,
        info: ResolveInfo,
        instance: models.Promotion,
        rules: list[models.PromotionRule],
        has_started: bool,
    ):
        app = get_app_promise(info.context).get()
        user = info.context.user
        events.promotion_created_event(instance, user, app)
        if rules:
            events.rule_created_event(user, app, rules)

        if has_started:
            events.promotion_started_event(instance, user, app)

    @classmethod
    def send_promotion_started_webhook(
        cls, manager: "PluginsManager", instance: models.Promotion
    ):
        """Send a webhook about starting promotion if it hasn't been sent yet."""

        now = datetime.now(pytz.utc)
        cls.call_event(manager.promotion_started, instance)
        instance.last_notification_scheduled_at = now
        instance.save(update_fields=["last_notification_scheduled_at"])
