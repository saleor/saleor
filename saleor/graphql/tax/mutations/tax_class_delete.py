import graphene

from ....permission.enums import CheckoutPermissions
from ....tax import error_codes, models
from ...core.descriptions import ADDED_IN_39
from ...core.doc_category import DOC_CATEGORY_TAXES
from ...core.mutations import ModelDeleteMutation
from ...core.types import Error
from ..types import TaxClass

TaxClassDeleteErrorCode = graphene.Enum.from_enum(error_codes.TaxClassDeleteErrorCode)
TaxClassDeleteErrorCode.doc_category = DOC_CATEGORY_TAXES


class TaxClassDeleteError(Error):
    code = TaxClassDeleteErrorCode(description="The error code.", required=True)

    class Meta:
        doc_category = DOC_CATEGORY_TAXES


class TaxClassDelete(ModelDeleteMutation):
    class Arguments:
        id = graphene.ID(required=True, description="ID of a tax class to delete.")

    class Meta:
        description = (
            "Delete a tax class. After deleting the tax class any products, "
            "product types or shipping methods using it are updated to use the "
            "default tax class."
        ) + ADDED_IN_39
        error_type_class = TaxClassDeleteError
        model = models.TaxClass
        object_type = TaxClass
        permissions = (CheckoutPermissions.MANAGE_TAXES,)
