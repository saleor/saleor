from django.core.exceptions import ValidationError
from django.utils.text import slugify
from text_unidecode import unidecode

from ....attribute import ATTRIBUTE_PROPERTIES_CONFIGURATION, AttributeInputType
from ....attribute import models as models
from ....attribute.error_codes import AttributeErrorCode
from ....core.utils import prepare_unique_slug
from ...core import ResolveInfo
from ...core.validators import validate_slug_and_generate_if_needed


class AttributeMixin:
    # must be redefined by inheriting classes
    ATTRIBUTE_VALUES_FIELD: str
    ONLY_SWATCH_FIELDS = ["file_url", "content_type", "value"]

    @classmethod
    def clean_values(cls, cleaned_input, attribute):
        """Clean attribute values.

        Transforms AttributeValueCreateInput into AttributeValue instances.
        Slugs are created from given names and checked for uniqueness within
        an attribute.
        """
        values_input = cleaned_input.get(cls.ATTRIBUTE_VALUES_FIELD)
        attribute_input_type = cleaned_input.get("input_type") or attribute.input_type

        if values_input is None:
            return

        if (
            values_input
            and attribute_input_type not in AttributeInputType.TYPES_WITH_CHOICES
        ):
            raise ValidationError(
                {
                    cls.ATTRIBUTE_VALUES_FIELD: ValidationError(
                        "Values cannot be used with "
                        f"input type {attribute_input_type}.",
                        code=AttributeErrorCode.INVALID.value,
                    )
                }
            )

        is_swatch_attr = attribute_input_type == AttributeInputType.SWATCH

        slug_list = list(
            attribute.values.values_list("slug", flat=True) if attribute.pk else []
        )

        for value_data in values_input:
            cls._validate_value(attribute, value_data, is_swatch_attr, slug_list)

        cls.check_values_are_unique(values_input, attribute)

    @classmethod
    def _validate_value(
        cls,
        attribute: models.Attribute,
        value_data: dict,
        is_swatch_attr: bool,
        slug_list: list,
    ):
        """Validate the new attribute value."""
        value = value_data.get("name")
        if value is None:
            raise ValidationError(
                {
                    cls.ATTRIBUTE_VALUES_FIELD: ValidationError(
                        "The name field is required.",
                        code=AttributeErrorCode.REQUIRED.value,
                    )
                }
            )

        if is_swatch_attr:
            cls.validate_swatch_attr_value(value_data)
        else:
            cls.validate_non_swatch_attr_value(value_data)

        slug_value = prepare_unique_slug(slugify(unidecode(value)), slug_list)
        value_data["slug"] = slug_value
        slug_list.append(slug_value)

        attribute_value = models.AttributeValue(**value_data, attribute=attribute)
        try:
            attribute_value.full_clean()
        except ValidationError as e:
            for field, err in e.error_dict.items():
                if field == "attribute":
                    continue
                errors = []
                for error in err:
                    error.code = AttributeErrorCode.INVALID.value
                    errors.append(error)
                raise ValidationError({cls.ATTRIBUTE_VALUES_FIELD: errors}) from e

    @classmethod
    def validate_non_swatch_attr_value(cls, value_data: dict):
        if any(value_data.get(field) for field in cls.ONLY_SWATCH_FIELDS):
            raise ValidationError(
                {
                    cls.ATTRIBUTE_VALUES_FIELD: ValidationError(
                        "Cannot define value, file and contentType fields "
                        "for not swatch attribute.",
                        code=AttributeErrorCode.INVALID.value,
                    )
                }
            )

    @classmethod
    def validate_swatch_attr_value(cls, value_data: dict):
        if value_data.get("value") and value_data.get("file_url"):
            raise ValidationError(
                {
                    cls.ATTRIBUTE_VALUES_FIELD: ValidationError(
                        "Cannot specify both value and file for swatch attribute.",
                        code=AttributeErrorCode.INVALID.value,
                    )
                }
            )

    @classmethod
    def check_values_are_unique(cls, values_input: dict, attribute: models.Attribute):
        # Check values uniqueness in case of creating new attribute.
        existing_names = (
            attribute.values.values_list("name", flat=True) if attribute.pk else []
        )
        existing_names = [name.lower().strip() for name in existing_names]
        for value_data in values_input:
            name = unidecode(value_data["name"]).lower().strip()
            if name in existing_names:
                msg = (
                    f"Value {value_data['name']} already exists within this attribute."
                )
                raise ValidationError(
                    {
                        cls.ATTRIBUTE_VALUES_FIELD: ValidationError(
                            msg, code=AttributeErrorCode.ALREADY_EXISTS.value
                        )
                    }
                )

        new_names = [value_data["name"].lower().strip() for value_data in values_input]
        if len(set(new_names)) != len(new_names):
            raise ValidationError(
                {
                    cls.ATTRIBUTE_VALUES_FIELD: ValidationError(
                        "Provided values are not unique.",
                        code=AttributeErrorCode.UNIQUE.value,
                    )
                }
            )

    @classmethod
    def clean_attribute(cls, instance, cleaned_input):
        try:
            cleaned_input = validate_slug_and_generate_if_needed(
                instance, "name", cleaned_input
            )
        except ValidationError as e:
            e.code = AttributeErrorCode.REQUIRED.value
            raise ValidationError({"slug": e}) from e
        cls._clean_attribute_settings(instance, cleaned_input)

        return cleaned_input

    @classmethod
    def _clean_attribute_settings(cls, instance, cleaned_input):
        """Validate attributes settings.

        Ensure that any invalid operations will be not performed.
        """
        attribute_input_type = cleaned_input.get("input_type") or instance.input_type
        errors = {}
        for field in ATTRIBUTE_PROPERTIES_CONFIGURATION.keys():
            allowed_input_type = ATTRIBUTE_PROPERTIES_CONFIGURATION[field]
            if attribute_input_type not in allowed_input_type and cleaned_input.get(
                field
            ):
                errors[field] = ValidationError(
                    f"Cannot set {field} on a {attribute_input_type} attribute.",
                    code=AttributeErrorCode.INVALID.value,
                )
        if errors:
            raise ValidationError(errors)

    @classmethod
    def _save_m2m(cls, info: ResolveInfo, attribute, cleaned_data):
        super()._save_m2m(info, attribute, cleaned_data)  # type: ignore[misc] # mixin
        values = cleaned_data.get(cls.ATTRIBUTE_VALUES_FIELD) or []
        for value in values:
            attribute.values.create(**value)
