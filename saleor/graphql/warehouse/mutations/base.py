from django.core.exceptions import ValidationError

from ....warehouse import WarehouseClickAndCollectOption
from ....warehouse.error_codes import WarehouseErrorCode
from ...core import ResolveInfo
from ...core.validators import (
    validate_required_string_field,
    validate_slug_and_generate_if_needed,
)


class WarehouseMixin:
    @classmethod
    def clean_input(cls, info: ResolveInfo, instance, data, **kwargs):
        cleaned_input = super().clean_input(  # type: ignore[misc] # mixin
            info, instance, data, **kwargs
        )
        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "name", cleaned_input
            )
        except ValidationError as error:
            error.code = WarehouseErrorCode.REQUIRED.value
            raise ValidationError({"slug": error})

        if "name" in cleaned_input:
            try:
                cleaned_input = validate_required_string_field(cleaned_input, "name")
            except ValidationError as error:
                error.code = WarehouseErrorCode.REQUIRED.value
                raise ValidationError({"name": error})

        # assigning shipping zones in the WarehouseCreate mutation is deprecated
        if cleaned_input.get("shipping_zones"):
            raise ValidationError(
                {
                    "shipping_zones": ValidationError(
                        "The shippingZone input field is deprecated. "
                        "Use WarehouseShippingZoneAssign mutation",
                        code=WarehouseErrorCode.INVALID.value,
                    )
                }
            )

        click_and_collect_option = cleaned_input.get(
            "click_and_collect_option", instance.click_and_collect_option
        )
        is_private = cleaned_input.get("is_private", instance.is_private)
        if (
            click_and_collect_option == WarehouseClickAndCollectOption.LOCAL_STOCK
            and is_private
        ):
            msg = "Local warehouse can be toggled only for non-private warehouse stocks"
            raise ValidationError(
                {
                    "click_and_collect_option": ValidationError(
                        msg, code=WarehouseErrorCode.INVALID.value
                    )
                },
            )
        return cleaned_input
