import datetime

from graphene import Field, ResolveInfo
from graphene.types.inputobjecttype import InputObjectType
from py.test import raises
from py.test import mark
from rest_framework import serializers

from ...types import DjangoObjectType
from ..models import MyFakeModel
from ..mutation import SerializerMutation


def mock_info():
    return ResolveInfo(
        None,
        None,
        None,
        None,
        schema=None,
        fragments=None,
        root_value=None,
        operation=None,
        variable_values=None,
        context=None,
    )


class MyModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = MyFakeModel
        fields = "__all__"


class MyModelMutation(SerializerMutation):
    class Meta:
        serializer_class = MyModelSerializer


class MySerializer(serializers.Serializer):
    text = serializers.CharField()
    model = MyModelSerializer()

    def create(self, validated_data):
        return validated_data


def test_needs_serializer_class():
    with raises(Exception) as exc:

        class MyMutation(SerializerMutation):
            pass

    assert str(exc.value) == "serializer_class is required for the SerializerMutation"


def test_has_fields():
    class MyMutation(SerializerMutation):
        class Meta:
            serializer_class = MySerializer

    assert "text" in MyMutation._meta.fields
    assert "model" in MyMutation._meta.fields
    assert "errors" in MyMutation._meta.fields


def test_has_input_fields():
    class MyMutation(SerializerMutation):
        class Meta:
            serializer_class = MySerializer

    assert "text" in MyMutation.Input._meta.fields
    assert "model" in MyMutation.Input._meta.fields


def test_exclude_fields():
    class MyMutation(SerializerMutation):
        class Meta:
            serializer_class = MyModelSerializer
            exclude_fields = ["created"]

    assert "cool_name" in MyMutation._meta.fields
    assert "created" not in MyMutation._meta.fields
    assert "errors" in MyMutation._meta.fields
    assert "cool_name" in MyMutation.Input._meta.fields
    assert "created" not in MyMutation.Input._meta.fields


def test_nested_model():
    class MyFakeModelGrapheneType(DjangoObjectType):
        class Meta:
            model = MyFakeModel

    class MyMutation(SerializerMutation):
        class Meta:
            serializer_class = MySerializer

    model_field = MyMutation._meta.fields["model"]
    assert isinstance(model_field, Field)
    assert model_field.type == MyFakeModelGrapheneType

    model_input = MyMutation.Input._meta.fields["model"]
    model_input_type = model_input._type.of_type
    assert issubclass(model_input_type, InputObjectType)
    assert "cool_name" in model_input_type._meta.fields
    assert "created" in model_input_type._meta.fields


def test_mutate_and_get_payload_success():
    class MyMutation(SerializerMutation):
        class Meta:
            serializer_class = MySerializer

    result = MyMutation.mutate_and_get_payload(
        None, mock_info(), **{"text": "value", "model": {"cool_name": "other_value"}}
    )
    assert result.errors is None


@mark.django_db
def test_model_add_mutate_and_get_payload_success():
    result = MyModelMutation.mutate_and_get_payload(
        None, mock_info(), **{"cool_name": "Narf"}
    )
    assert result.errors is None
    assert result.cool_name == "Narf"
    assert isinstance(result.created, datetime.datetime)


@mark.django_db
def test_model_update_mutate_and_get_payload_success():
    instance = MyFakeModel.objects.create(cool_name="Narf")
    result = MyModelMutation.mutate_and_get_payload(
        None, mock_info(), **{"id": instance.id, "cool_name": "New Narf"}
    )
    assert result.errors is None
    assert result.cool_name == "New Narf"


@mark.django_db
def test_model_invalid_update_mutate_and_get_payload_success():
    class InvalidModelMutation(SerializerMutation):
        class Meta:
            serializer_class = MyModelSerializer
            model_operations = ["update"]

    with raises(Exception) as exc:
        result = InvalidModelMutation.mutate_and_get_payload(
            None, mock_info(), **{"cool_name": "Narf"}
        )

    assert '"id" required' in str(exc.value)


def test_mutate_and_get_payload_error():
    class MyMutation(SerializerMutation):
        class Meta:
            serializer_class = MySerializer

    # missing required fields
    result = MyMutation.mutate_and_get_payload(None, mock_info(), **{})
    assert len(result.errors) > 0


def test_model_mutate_and_get_payload_error():
    # missing required fields
    result = MyModelMutation.mutate_and_get_payload(None, mock_info(), **{})
    assert len(result.errors) > 0


def test_invalid_serializer_operations():
    with raises(Exception) as exc:

        class MyModelMutation(SerializerMutation):
            class Meta:
                serializer_class = MyModelSerializer
                model_operations = ["Add"]

    assert "model_operations" in str(exc.value)
