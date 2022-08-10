from django.db import IntegrityError, models
from graphene import Int

from ..core.models import ModelWithMetadata
from ..core.permissions.enums import TaxPermissions

DEFAULT_TAX_CLASS_NAME = "Default"


def get_default_tax_class() -> Int:
    """Get the ID of the default tax class.

    The function gets or creates a default tax class and returns it's ID. It is
    intended to be used as a default tax class in foreign key relations.
    """
    tax_class, _ = TaxClass.objects.get_or_create(
        is_default=True, name=DEFAULT_TAX_CLASS_NAME
    )
    return tax_class.pk


class TaxClass(ModelWithMetadata):
    name = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)

    class Meta:
        ordering = ("is_default", "name", "pk")
        permissions = (
            (
                TaxPermissions.MANAGE_TAXES.codename,
                "Manage taxes.",
            ),
        )

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        if self.is_default:
            raise IntegrityError("Cannot remove a default tax class.")
        return super().delete(*args, **kwargs)
