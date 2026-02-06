import pytest
from django.core.exceptions import ValidationError

from ..limited_string import LimitedString
from ..types.base import BaseInputObjectType
from ..validators import validate_string_constraints

# --- LimitedString helper tests ---


def test_limited_string_description_with_min_only():
    field = LimitedString(min_length=3, description="Name.")
    assert field.kwargs["description"] == "Name. (Minimum 3 characters.)"


def test_limited_string_description_with_max_only():
    field = LimitedString(max_length=100, description="Name.")
    assert field.kwargs["description"] == "Name. (maximum 100 characters.)"


def test_limited_string_description_with_both():
    field = LimitedString(min_length=1, max_length=250, description="Product name.")
    assert (
        field.kwargs["description"]
        == "Product name. (Minimum 1, maximum 250 characters.)"
    )


def test_limited_string_description_without_explicit_description():
    field = LimitedString(min_length=5, max_length=50)
    assert field.kwargs["description"] == " (Minimum 5, maximum 50 characters.)"


def test_limited_string_stores_constraint_attributes():
    field = LimitedString(min_length=2, max_length=100)
    assert field._limited_min_length == 2
    assert field._limited_max_length == 100


def test_limited_string_stores_none_for_unset_constraints():
    field = LimitedString(max_length=50)
    assert field._limited_min_length is None
    assert field._limited_max_length == 50


def test_limited_string_asserts_min_length_less_than_one():
    with pytest.raises(AssertionError, match="min_length must be >= 1"):
        LimitedString(min_length=0)


def test_limited_string_asserts_max_length_less_than_one():
    with pytest.raises(AssertionError, match="max_length must be >= 1"):
        LimitedString(max_length=0)


def test_limited_string_asserts_min_greater_than_max():
    with pytest.raises(AssertionError, match="min_length must be <= max_length"):
        LimitedString(min_length=10, max_length=5)


# --- BaseInputObjectType constraint capture tests ---


def test_base_input_captures_string_constraints():
    class MyInput(BaseInputObjectType):
        name = LimitedString(min_length=1, max_length=100)

    assert hasattr(MyInput, "_string_constraints")
    assert MyInput._string_constraints == {"name": (1, 100)}


def test_base_input_inherits_parent_constraints():
    class ParentInput(BaseInputObjectType):
        name = LimitedString(min_length=1, max_length=100)

    class ChildInput(ParentInput):
        slug = LimitedString(max_length=50)

    assert ChildInput._string_constraints == {
        "name": (1, 100),
        "slug": (None, 50),
    }


def test_base_input_child_overrides_parent_constraint():
    class ParentInput(BaseInputObjectType):
        name = LimitedString(min_length=1, max_length=100)

    class ChildInput(ParentInput):
        name = LimitedString(min_length=1, max_length=200)

    assert ChildInput._string_constraints["name"] == (1, 200)


def test_base_input_no_constraints_when_no_limited_string():
    class PlainInput(BaseInputObjectType):
        pass

    assert not hasattr(PlainInput, "_string_constraints")


# --- validate_string_constraints tests ---


def test_validate_string_constraints_raises_for_too_short():
    class MyInput(BaseInputObjectType):
        name = LimitedString(min_length=3, max_length=100)

    with pytest.raises(ValidationError) as exc_info:
        validate_string_constraints(MyInput, {"name": "ab"})

    assert "name" in exc_info.value.message_dict
    error = exc_info.value.message_dict["name"][0]
    assert "at least 3 characters" in error


def test_validate_string_constraints_raises_for_too_long():
    class MyInput(BaseInputObjectType):
        name = LimitedString(min_length=1, max_length=5)

    with pytest.raises(ValidationError) as exc_info:
        validate_string_constraints(MyInput, {"name": "toolong"})

    assert "name" in exc_info.value.message_dict
    error = exc_info.value.message_dict["name"][0]
    assert "at most 5 characters" in error


def test_validate_string_constraints_passes_for_valid():
    class MyInput(BaseInputObjectType):
        name = LimitedString(min_length=1, max_length=10)

    # Should not raise
    validate_string_constraints(MyInput, {"name": "valid"})


def test_validate_string_constraints_skips_none_values():
    class MyInput(BaseInputObjectType):
        name = LimitedString(min_length=1, max_length=10)

    # Should not raise
    validate_string_constraints(MyInput, {"name": None})


def test_validate_string_constraints_skips_missing_fields():
    class MyInput(BaseInputObjectType):
        name = LimitedString(min_length=1, max_length=10)

    # Should not raise
    validate_string_constraints(MyInput, {})


def test_validate_string_constraints_no_constraints():
    class PlainInput(BaseInputObjectType):
        pass

    # Should not raise
    validate_string_constraints(PlainInput, {"name": "anything"})


def test_validate_string_constraints_at_boundary_min():
    class MyInput(BaseInputObjectType):
        name = LimitedString(min_length=3, max_length=10)

    # Exactly min_length should pass
    validate_string_constraints(MyInput, {"name": "abc"})


def test_validate_string_constraints_at_boundary_max():
    class MyInput(BaseInputObjectType):
        name = LimitedString(min_length=1, max_length=5)

    # Exactly max_length should pass
    validate_string_constraints(MyInput, {"name": "abcde"})


def test_validate_string_constraints_multiple_fields_errors():
    class MyInput(BaseInputObjectType):
        name = LimitedString(min_length=3, max_length=100)
        slug = LimitedString(max_length=5)

    with pytest.raises(ValidationError) as exc_info:
        validate_string_constraints(MyInput, {"name": "ab", "slug": "toolong"})

    errors = exc_info.value.message_dict
    assert "name" in errors
    assert "slug" in errors
