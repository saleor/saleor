from collections import defaultdict
from typing import DefaultDict, List, Tuple

import graphene
from django.core.exceptions import ValidationError
from django.db import transaction
from graphql.error import GraphQLError

from .....channel import models as channel_models
from .....discount import models
from .....permission.enums import DiscountPermissions
from ....channel.types import Channel
from ....core import ResolveInfo
from ....core.descriptions import ADDED_IN_315, PREVIEW_FEATURE
from ....core.doc_category import DOC_CATEGORY_DISCOUNTS
from ....core.mutations import ModelMutation
from ....core.scalars import JSON, PositiveDecimal
from ....core.types import BaseInputObjectType, Error, NonNullList
from ....core.validators import validate_end_is_after_start
from ....plugins.dataloaders import get_plugin_manager_promise
from ....utils import get_nodes
from ...enums import PromotionCreateErrorCode, RewardValueTypeEnum
from ...inputs import CataloguePredicateInput
from ...types import Promotion
from ...utils import clean_predicate


class PromotionCreateError(Error):
    code = PromotionCreateErrorCode(description="The error code.", required=True)
    index = graphene.Int(
        description="Index of an input list item that caused the error."
    )


class PromotionRuleInput(BaseInputObjectType):
    name = graphene.String(description="Promotion rule name.")
    description = JSON(description="Promotion rule description.")
    channels = NonNullList(
        graphene.ID,
        description="List of channel ids to which the rule should apply to.",
    )
    catalogue_predicate = CataloguePredicateInput(
        description=(
            "Defines the conditions on the catalogue level that must be met "
            "for the reward to be applied."
        ),
    )
    reward_value_type = RewardValueTypeEnum(
        description=(
            "Defines the promotion rule reward value type. "
            "Must be provided together with reward value."
        ),
    )
    reward_value = PositiveDecimal(
        description=(
            "Defines the discount value. Required when catalogue predicate is provided."
        ),
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
        description = "Creates a new promotion." + ADDED_IN_315 + PREVIEW_FEATURE
        model = models.Promotion
        object_type = Promotion
        permissions = (DiscountPermissions.MANAGE_DISCOUNTS,)
        error_type_class = PromotionCreateError
        doc_category = DOC_CATEGORY_DISCOUNTS

    @classmethod
    def clean_input(
        cls, info: ResolveInfo, instance: models.Promotion, data: dict, **kwargs
    ):
        cleaned_input = super().clean_input(info, instance, data, **kwargs)

        errors: DefaultDict[str, List[ValidationError]] = defaultdict(list)
        start_date = cleaned_input.get("start_date")
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
        errors: DefaultDict[str, List[ValidationError]],
    ) -> Tuple[list, DefaultDict[str, List[ValidationError]]]:
        cleaned_rules = []
        for index, rule_data in enumerate(rules_data):
            if channel_ids := rule_data.get("channels"):
                channels = cls.clean_channels(info, channel_ids, index, errors)
                rule_data["channels"] = channels

            if "catalogue_predicate" not in rule_data:
                errors["catalogue_predicate"].append(
                    ValidationError(
                        "The field is required.",
                        code=PromotionCreateErrorCode.REQUIRED.value,
                        params={"index": index},
                    )
                )
            else:
                if "reward_value_type" not in rule_data:
                    errors["reward_value_type"].append(
                        ValidationError(
                            "The rewardValueType is required for when "
                            "cataloguePredicate is provided.",
                            code=PromotionCreateErrorCode.REQUIRED.value,
                            params={"index": index},
                        )
                    )
                if "reward_value" not in rule_data:
                    errors["reward_value"].append(
                        ValidationError(
                            "The rewardValue is required for when cataloguePredicate "
                            "is provided.",
                            code=PromotionCreateErrorCode.REQUIRED.value,
                            params={"index": index},
                        )
                    )
                rule_data["catalogue_predicate"] = clean_predicate(
                    rule_data.get("catalogue_predicate")
                )
            cleaned_rules.append(rule_data)

        return cleaned_rules, errors

    @classmethod
    def clean_channels(
        cls,
        info: ResolveInfo,
        channel_ids: List[str],
        index: int,
        errors: DefaultDict[str, List[ValidationError]],
    ) -> List[channel_models.Channel]:
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
        manager = get_plugin_manager_promise(info.context).get()

        cls.clean_instance(info, instance)
        with transaction.atomic():
            cls.save(info, instance, cleaned_input)
            cls._save_m2m(info, instance, cleaned_input)
            cls.send_sale_notifications(manager, instance)
        return cls.success_response(instance)

    @classmethod
    def _save_m2m(
        cls, info: ResolveInfo, instance: models.Promotion, cleaned_data: dict
    ):
        super()._save_m2m(info, instance, cleaned_data)
        rules_with_channels_to_add = []
        if rules_data := cleaned_data.get("rules"):
            rules = []
            for rule_data in rules_data:
                channels = rule_data.pop("channels", None)
                rule = models.PromotionRule(promotion=instance, **rule_data)
                rules_with_channels_to_add.append((rule, channels))
                rules.append(rule)
            models.PromotionRule.objects.bulk_create(rules)

        for rule, channels in rules_with_channels_to_add:
            rule.channels.set(channels)

    @classmethod
    def send_sale_notifications(cls, manager, instance):
        # TODO: implement the notifications
        pass
