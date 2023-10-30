import graphene
import pytest
from django import forms

from ..types.converter import convert_form_field, get_form_field_description

nonempty_text = "Some text"


@pytest.fixture
def mockfield():
    class Field:
        pass

    return Field()


def test_get_form_field_description_empty_help_text(mockfield):
    # given
    mockfield.help_text = ""

    # when
    result = get_form_field_description(mockfield)

    # then
    assert result is None


def test_get_form_field_description_nonempty_help_text(mockfield):
    # given
    mockfield.help_text = nonempty_text

    # when
    result = get_form_field_description(mockfield)

    # then
    assert result == nonempty_text


def test_get_form_field_description_empty_extra_help_text(mockfield):
    # given
    mockfield.extra = {"help_text": ""}

    # when
    result = get_form_field_description(mockfield)

    # then
    assert result is None


def test_get_form_field_description_nonempty_extra_help_text(mockfield):
    # given
    mockfield.extra = {"help_text": nonempty_text}

    # when
    result = get_form_field_description(mockfield)

    # then
    assert result == nonempty_text


@pytest.mark.parametrize(
    ("infield", "outfield_type", "expected_description"),
    [
        # given
        (forms.CharField(), graphene.String, None),
        (forms.CharField(help_text=nonempty_text), graphene.String, nonempty_text),
        (forms.NullBooleanField(), graphene.Boolean, None),
        (
            forms.NullBooleanField(help_text=nonempty_text),
            graphene.Boolean,
            nonempty_text,
        ),
        (forms.DecimalField(), graphene.Float, None),
        (forms.DecimalField(help_text=nonempty_text), graphene.Float, nonempty_text),
        (forms.FloatField(), graphene.Float, None),
        (forms.FloatField(help_text=nonempty_text), graphene.Float, nonempty_text),
    ],
)
def test_conversion(infield, outfield_type, expected_description):
    # when
    converted = convert_form_field(infield)

    # then
    assert isinstance(converted, outfield_type)
    if expected_description is not None:
        if not hasattr(converted, "description"):
            assert converted.kwargs["description"] == expected_description
        else:
            assert converted.description == expected_description
    elif hasattr(converted, "description"):
        assert converted.description is None
