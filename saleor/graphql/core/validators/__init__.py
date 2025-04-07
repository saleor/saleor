from typing import TYPE_CHECKING, Optional
from uuid import UUID

import graphene
from babel.numbers import get_currency_precision
from django.conf import settings
from django.core.exceptions import ValidationError
from graphene.utils.str_converters import to_camel_case
from graphql.error import GraphQLError

from ....core.utils import generate_unique_slug
from ....product.models import ProductVariantChannelListing

if TYPE_CHECKING:
    from decimal import Decimal

    from django.db.models import Model


def validate_one_of_args_is_in_mutation(*args, **kwargs):
    try:
        validate_one_of_args_is_in_query(*args, **kwargs)
    except GraphQLError as e:
        raise ValidationError(str(e), code="graphql_error") from e


def validate_one_of_args_is_in_query(*args, **kwargs):
    # split args into a list with 2-element tuples:
    # [(arg1_name, arg1_value), (arg2_name, arg2_value), ...]
    splitted_args = [args[i : i + 2] for i in range(0, len(args), 2)]  # noqa: E203
    # filter trueish values from each tuple
    filter_args = list(filter(lambda item: bool(item[1]) is True, splitted_args))
    use_camel_case = kwargs.get("use_camel_case")

    if len(filter_args) > 1:
        if use_camel_case:
            first_arg = to_camel_case(filter_args[0][0])
            rest_args = ", ".join(
                [f"'{to_camel_case(item[0])}'" for item in filter_args[1:]]
            )
        else:
            first_arg = filter_args[0][0]
            rest_args = ", ".join([f"'{item[0]}'" for item in filter_args[1:]])
        raise GraphQLError(
            f"Argument '{first_arg}' cannot be combined with {rest_args}"
        )

    if not filter_args:
        if use_camel_case:
            required_args = ", ".join(
                [f"'{to_camel_case(item[0])}'" for item in splitted_args]
            )
        else:
            required_args = ", ".join([f"'{item[0]}'" for item in splitted_args])
        raise GraphQLError(f"At least one of arguments is required: {required_args}.")


def validate_price_precision(
    value: Optional["Decimal"],
    currency: str,
    currency_fractions=None,
):
    """Validate if price amount does not have too many decimal places.

    Price amount can't have more decimal places than currency allow to.
    Works only with decimal created from a string.
    """

    # check no needed when there is no value
    if not value:
        return

    if currency_fractions:
        try:
            currency_fraction = currency_fractions[currency][0]
        except KeyError:
            currency_fraction = currency_fractions["DEFAULT"][0]
    else:
        currency_fraction = get_currency_precision(currency)

    value = value.normalize()
    if value.as_tuple().exponent < -currency_fraction:
        raise ValidationError(
            f"Value cannot have more than {currency_fraction} decimal places."
        )


def validate_decimal_max_value(value: "Decimal", max_value=10**9):
    """Validate if price amount is not higher than the limit for precision field.

    Decimal fields in database have value limits.
    By default its 10^9 for fields with precision 12.
    """
    if value >= max_value:
        raise ValidationError(f"Value must be lower than {max_value}.")


def get_not_available_variants_in_channel(
    variants_id: set,
    channel_id: int,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
) -> tuple[set[int], set[str]]:
    available_variants = (
        ProductVariantChannelListing.objects.using(database_connection_name)
        .filter(
            variant__id__in=variants_id,
            channel_id=channel_id,
            price_amount__isnull=False,
        )
        .values_list("variant_id", flat=True)
    )
    not_available_variants = variants_id - set(available_variants)
    not_available_graphql_ids = {
        graphene.Node.to_global_id("ProductVariant", pk)
        for pk in not_available_variants
    }
    return not_available_variants, not_available_graphql_ids


def validate_variants_available_in_channel(
    variants_id: set,
    channel_id: int,
    error_code: str,
    database_connection_name: str = settings.DATABASE_CONNECTION_DEFAULT_NAME,
):
    """Validate available variants in specific channel."""
    (
        not_available_variants,
        not_available_graphql_ids,
    ) = get_not_available_variants_in_channel(
        variants_id, channel_id, database_connection_name
    )
    if not_available_variants:
        raise ValidationError(
            {
                "lines": ValidationError(
                    "Cannot add lines with unavailable variants.",
                    code=error_code,
                    params={"variants": not_available_graphql_ids},
                )
            }
        )


def validate_end_is_after_start(start_date, end_date):
    """Validate if the end date provided is after start date."""

    # check is not needed if no end date
    if end_date is None:
        return

    if start_date > end_date:
        raise ValidationError("End date cannot be before the start date.")


def validate_slug_and_generate_if_needed(
    instance: "Model",
    slugable_field: str,
    cleaned_input: dict,
    slug_field_name: str = "slug",
) -> dict:
    """Validate slug from input and generate in create mutation if is not given."""

    # update mutation - just check if slug value is not empty
    # _state.adding is True only when it's new not saved instance.
    if not instance._state.adding:
        validate_slug_value(cleaned_input)
        return cleaned_input

    # create mutation - generate slug if slug value is empty
    slug = cleaned_input.get(slug_field_name)
    if not slug and slugable_field in cleaned_input:
        slug = generate_unique_slug(instance, cleaned_input[slugable_field])
        cleaned_input[slug_field_name] = slug
    return cleaned_input


def validate_slug_value(cleaned_input, slug_field_name: str = "slug"):
    if slug_field_name in cleaned_input:
        slug = cleaned_input[slug_field_name]
        if not slug:
            raise ValidationError(
                f"{slug_field_name.capitalize()} value cannot be blank."
            )


def clean_seo_fields(data):
    """Extract and assign seo fields to given dictionary."""
    seo_fields = data.pop("seo", {})

    if seo_fields:
        if "title" in seo_fields:
            data["seo_title"] = seo_fields["title"]

        if "description" in seo_fields:
            data["seo_description"] = seo_fields["description"]


def validate_required_string_field(cleaned_input, field_name: str):
    """Strip and validate field value."""
    field_value = cleaned_input.get(field_name)
    field_value = field_value.strip() if field_value else ""
    if field_value:
        cleaned_input[field_name] = field_value
    else:
        raise ValidationError(f"{field_name.capitalize()} is required.")
    return cleaned_input


def validate_if_int_or_uuid(id):
    try:
        int(id)
    except ValueError:
        try:
            UUID(id)
        except (AttributeError, ValueError) as e:
            raise ValidationError("Must receive an int or UUID.") from e
