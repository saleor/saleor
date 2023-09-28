from typing import TYPE_CHECKING, Union

from django.core.exceptions import ValidationError
from graphene.utils.str_converters import to_camel_case

from .....discount import RewardValueType
from ....core.validators import validate_price_precision

if TYPE_CHECKING:
    from decimal import Decimal


def clean_promotion_rule(cleaned_input, errors, error_class, index=None):
    if "catalogue_predicate" not in cleaned_input:
        errors["catalogue_predicate"].append(
            ValidationError(
                "The cataloguePredicate field is required.",
                code=error_class.REQUIRED.value,
                params={"index": index} if index is not None else {},
            )
        )
    else:
        clean_reward(cleaned_input, errors, error_class, index)

        try:
            cleaned_input["catalogue_predicate"] = clean_predicate(
                cleaned_input.get("catalogue_predicate"),
                error_class,
                index,
            )
        except ValidationError as error:
            errors["catalogue_predicate"].append(error)


def clean_reward(cleaned_input, errors, error_class, index=None):
    reward_value = cleaned_input.get("reward_value")
    reward_value_type = cleaned_input.get("reward_value_type")
    if reward_value_type is None:
        errors["reward_value_type"].append(
            ValidationError(
                "The rewardValueType is required for when "
                "cataloguePredicate is provided.",
                code=error_class.REQUIRED.value,
                params={"index": index} if index is not None else {},
            )
        )
    if reward_value is None:
        errors["reward_value"].append(
            ValidationError(
                "The rewardValue is required when cataloguePredicate is provided.",
                code=error_class.REQUIRED.value,
                params={"index": index} if index is not None else {},
            )
        )
    if reward_value and reward_value_type:
        clean_reward_value(
            reward_value,
            reward_value_type,
            cleaned_input.get("channels"),
            errors,
            error_class,
            index,
        )


def clean_reward_value(
    reward_value, reward_value_type, channels, errors, error_class, index=None
):
    if reward_value_type == RewardValueType.FIXED:
        if "channels" in errors:
            return
        if not channels:
            errors["channels"].append(
                ValidationError(
                    "Channels must be specified for FIXED rewardValueType.",
                    code=error_class.REQUIRED.value,
                    params={"index": index} if index is not None else {},
                )
            )
            return
        currencies = {channel.currency_code for channel in channels}
        if len(currencies) > 1:
            error_code = error_class.MULTIPLE_CURRENCIES_NOT_ALLOWED.value
            errors["reward_value_type"].append(
                ValidationError(
                    "For FIXED rewardValueType, all channels must have "
                    "the same currency.",
                    code=error_code,
                    params={"index": index} if index is not None else {},
                )
            )
            return

        currency = currencies.pop()
        try:
            clean_fixed_discount_value(
                reward_value,
                error_class.INVALID_PRECISION.value,
                currency,
                index,
            )
        except ValidationError as error:
            errors["reward_value"].append(error)

    elif reward_value_type == RewardValueType.PERCENTAGE:
        try:
            clean_percentage_discount_value(
                reward_value, error_class.INVALID.value, index
            )
        except ValidationError as error:
            errors["reward_value"].append(error)


def clean_predicate(predicate, error_class, index=None):
    """Validate operators and convert snake cases keys into camel case.

    Operators cannot be mixed with other filter inputs. There could be only
    one operator on each level.
    """
    if isinstance(predicate, list):
        return [
            clean_predicate(item, error_class, index)
            if isinstance(item, (dict, list))
            else item
            for item in predicate
        ]
    # when any operator appear there cannot be any more data in filter input
    if _contains_operator(predicate) and len(predicate.keys()) > 1:
        raise ValidationError(
            "Cannot mix operators with other filter inputs.",
            code=error_class.INVALID.value,
            params={"index": index} if index is not None else {},
        )
    return {
        to_camel_case(key): clean_predicate(value, error_class, index)
        if isinstance(value, (dict, list))
        else value
        for key, value in predicate.items()
    }


def _contains_operator(input: dict[str, Union[dict, str]]):
    return any([operator in input for operator in ["AND", "OR"]])


def clean_fixed_discount_value(
    reward_value: "Decimal", error_code: str, currency_code: str, index=None
):
    try:
        validate_price_precision(reward_value, currency_code)
    except ValidationError:
        raise ValidationError(
            "Invalid amount precision.",
            code=error_code,
            params={"index": index} if index is not None else {},
        )


def clean_percentage_discount_value(
    reward_value: "Decimal", error_code: str, index=None
):
    if reward_value > 100:
        raise ValidationError(
            "Invalid percentage value.",
            code=error_code,
            params={"index": index} if index is not None else {},
        )
