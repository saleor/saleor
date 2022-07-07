import pytest
from django.db import IntegrityError

from ..models import TaxClass


def test_deleting_default_tax_class_raises_error():
    default_tax_class = TaxClass.objects.filter(is_default=True).first()
    with pytest.raises(IntegrityError):
        default_tax_class.delete()
