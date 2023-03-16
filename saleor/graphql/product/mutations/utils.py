from django.db.models import Q

from ....plugins.manager import PluginsManager
from ....tax.models import TaxClass

"""
Clean deprecated `taxCode` field.

This function provides backwards compatibility for the `taxCode` input field. If the
`taxClass` is not provided but the `taxCode` is, try to find a tax class with given
tax code and assign it to the product type. If no matching tax class is found, create
one with the given tax code.
"""


def clean_tax_code(cleaned_input: dict, manager: PluginsManager):
    tax_code = cleaned_input.get("tax_code")
    if tax_code and "tax_class" not in cleaned_input:
        tax_code = cleaned_input["tax_code"]
        tax_class = TaxClass.objects.filter(
            Q(name=tax_code)
            | Q(metadata__contains={"avatax.code": tax_code})
            | Q(metadata__contains={"vatlayer.code": tax_code})
        ).first()
        if not tax_class:
            tax_class = TaxClass.objects.create(name=tax_code)
            manager.assign_tax_code_to_object_meta(tax_class, tax_code)
            tax_class.save(update_fields=["metadata"])
        cleaned_input["tax_class"] = tax_class
