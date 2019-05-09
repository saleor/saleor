from py.test import raises

from ..registry import Registry
from ..types import DjangoObjectType
from .models import Reporter


def test_should_raise_if_no_model():
    with raises(Exception) as excinfo:

        class Character1(DjangoObjectType):
            pass

    assert "valid Django Model" in str(excinfo.value)


def test_should_raise_if_model_is_invalid():
    with raises(Exception) as excinfo:

        class Character2(DjangoObjectType):
            class Meta:
                model = 1

    assert "valid Django Model" in str(excinfo.value)


def test_should_map_fields_correctly():
    class ReporterType2(DjangoObjectType):
        class Meta:
            model = Reporter
            registry = Registry()

    fields = list(ReporterType2._meta.fields.keys())
    assert fields[:-2] == [
        "id",
        "first_name",
        "last_name",
        "email",
        "pets",
        "a_choice",
        "reporter_type",
    ]

    assert sorted(fields[-2:]) == ["articles", "films"]


def test_should_map_only_few_fields():
    class Reporter2(DjangoObjectType):
        class Meta:
            model = Reporter
            only_fields = ("id", "email")

    assert list(Reporter2._meta.fields.keys()) == ["id", "email"]
