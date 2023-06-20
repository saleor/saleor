import graphene
from django.core.exceptions import ValidationError

from ....order.error_codes import OrderNoteAddErrorCode
from ...core.doc_category import DOC_CATEGORY_ORDERS
from ...core.mutations import BaseMutation
from ...core.types import BaseInputObjectType
from ...core.validators import validate_required_string_field


class OrderNoteInput(BaseInputObjectType):
    message = graphene.String(
        description="Note message.", name="message", required=True
    )

    class Meta:
        doc_category = DOC_CATEGORY_ORDERS


class OrderNoteCommon(BaseMutation):
    class Arguments:
        input = OrderNoteInput(
            required=True, description="Fields required to create a note for the order."
        )

    class Meta:
        abstract = True

    @classmethod
    def clean_input(cls, _info, _instance, data):
        try:
            cleaned_input = validate_required_string_field(data, "message")
        except ValidationError:
            raise ValidationError(
                {
                    "message": ValidationError(
                        "Message can't be empty.",
                        code=OrderNoteAddErrorCode.REQUIRED.value,
                    )
                }
            )
        return cleaned_input
