from django.db.models import Q

from ....plugins.manager import PluginsManager
from ....tax.models import TaxClass


def clean_tax_code(cleaned_input: dict, manager: PluginsManager):
    """Clean deprecated `taxCode` field.

    This function provides backwards compatibility for the `taxCode` input field. If the
    `taxClass` is not provided but the `taxCode` is, try to find a tax class with given
    tax code and assign it to the product type.
    """
    tax_code = cleaned_input.get("tax_code")
    if tax_code and "tax_class" not in cleaned_input:
        tax_class = TaxClass.objects.filter(
            Q(name=tax_code)
            | Q(metadata__contains={"avatax.code": tax_code})
            | Q(metadata__contains={"vatlayer.code": tax_code})
        ).first()
        cleaned_input["tax_class"] = tax_class
