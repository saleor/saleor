from django.core.exceptions import ValidationError

from .....core.editorjs import editorjs_to_text
from .....product.error_codes import ProductErrorCode
from ....core.validators import validate_slug_and_generate_if_needed


def clean_weight(cleaned_input: dict):
    weight = cleaned_input.get("weight")
    if weight and weight.value < 0:
        raise ValidationError(
            {
                "weight": ValidationError(
                    "Product can't have negative weight.",
                    code=ProductErrorCode.INVALID.value,
                )
            }
        )


def clean_slug(cleaned_input: dict, instance):
    try:
        validate_slug_and_generate_if_needed(instance, "name", cleaned_input)
    except ValidationError as e:
        e.code = ProductErrorCode.REQUIRED.value
        raise ValidationError({"slug": e}) from e


def clean_description(cleaned_input: dict):
    if "description" in cleaned_input:
        description = cleaned_input["description"]
        cleaned_input["description_plaintext"] = (
            editorjs_to_text(description) if description else ""
        )
