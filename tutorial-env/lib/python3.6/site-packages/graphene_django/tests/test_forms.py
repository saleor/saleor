from django.core.exceptions import ValidationError
from py.test import raises

from ..forms import GlobalIDFormField, GlobalIDMultipleChoiceField


# 'TXlUeXBlOmFiYw==' -> 'MyType', 'abc'


def test_global_id_valid():
    field = GlobalIDFormField()
    field.clean("TXlUeXBlOmFiYw==")


def test_global_id_invalid():
    field = GlobalIDFormField()
    with raises(ValidationError):
        field.clean("badvalue")


def test_global_id_multiple_valid():
    field = GlobalIDMultipleChoiceField()
    field.clean(["TXlUeXBlOmFiYw==", "TXlUeXBlOmFiYw=="])


def test_global_id_multiple_invalid():
    field = GlobalIDMultipleChoiceField()
    with raises(ValidationError):
        field.clean(["badvalue", "another bad avue"])


def test_global_id_none():
    field = GlobalIDFormField()
    with raises(ValidationError):
        field.clean(None)


def test_global_id_none_optional():
    field = GlobalIDFormField(required=False)
    field.clean(None)
