import pytest
from django.db import models
from django.utils.translation import ugettext_lazy as _
from py.test import raises

import graphene
from graphene.relay import ConnectionField, Node
from graphene.types.datetime import DateTime, Date, Time
from graphene.types.json import JSONString

from ..compat import JSONField, ArrayField, HStoreField, RangeField, MissingType
from ..converter import convert_django_field, convert_django_field_with_choices
from ..registry import Registry
from ..types import DjangoObjectType
from .models import Article, Film, FilmDetails, Reporter


# from graphene.core.types.custom_scalars import DateTime, Time, JSONString


def assert_conversion(django_field, graphene_field, *args, **kwargs):
    field = django_field(help_text="Custom Help Text", null=True, *args, **kwargs)
    graphene_type = convert_django_field(field)
    assert isinstance(graphene_type, graphene_field)
    field = graphene_type.Field()
    assert field.description == "Custom Help Text"
    nonnull_field = django_field(null=False, *args, **kwargs)
    if not nonnull_field.null:
        nonnull_graphene_type = convert_django_field(nonnull_field)
        nonnull_field = nonnull_graphene_type.Field()
        assert isinstance(nonnull_field.type, graphene.NonNull)
        return nonnull_field
    return field


def test_should_unknown_django_field_raise_exception():
    with raises(Exception) as excinfo:
        convert_django_field(None)
    assert "Don't know how to convert the Django field" in str(excinfo.value)


def test_should_date_time_convert_string():
    assert_conversion(models.DateTimeField, DateTime)


def test_should_date_convert_string():
    assert_conversion(models.DateField, Date)


def test_should_time_convert_string():
    assert_conversion(models.TimeField, Time)


def test_should_char_convert_string():
    assert_conversion(models.CharField, graphene.String)


def test_should_text_convert_string():
    assert_conversion(models.TextField, graphene.String)


def test_should_email_convert_string():
    assert_conversion(models.EmailField, graphene.String)


def test_should_slug_convert_string():
    assert_conversion(models.SlugField, graphene.String)


def test_should_url_convert_string():
    assert_conversion(models.URLField, graphene.String)


def test_should_ipaddress_convert_string():
    assert_conversion(models.GenericIPAddressField, graphene.String)


def test_should_file_convert_string():
    assert_conversion(models.FileField, graphene.String)


def test_should_image_convert_string():
    assert_conversion(models.ImageField, graphene.String)


def test_should_url_convert_string():
    assert_conversion(models.FilePathField, graphene.String)


def test_should_auto_convert_id():
    assert_conversion(models.AutoField, graphene.ID, primary_key=True)


def test_should_auto_convert_id():
    assert_conversion(models.UUIDField, graphene.UUID)


def test_should_auto_convert_duration():
    assert_conversion(models.DurationField, graphene.Float)


def test_should_positive_integer_convert_int():
    assert_conversion(models.PositiveIntegerField, graphene.Int)


def test_should_positive_small_convert_int():
    assert_conversion(models.PositiveSmallIntegerField, graphene.Int)


def test_should_small_integer_convert_int():
    assert_conversion(models.SmallIntegerField, graphene.Int)


def test_should_big_integer_convert_int():
    assert_conversion(models.BigIntegerField, graphene.Int)


def test_should_integer_convert_int():
    assert_conversion(models.IntegerField, graphene.Int)


def test_should_boolean_convert_boolean():
    field = assert_conversion(models.BooleanField, graphene.NonNull)
    assert field.type.of_type == graphene.Boolean


def test_should_nullboolean_convert_boolean():
    assert_conversion(models.NullBooleanField, graphene.Boolean)


def test_field_with_choices_convert_enum():
    field = models.CharField(
        help_text="Language", choices=(("es", "Spanish"), ("en", "English"))
    )

    class TranslatedModel(models.Model):
        language = field

        class Meta:
            app_label = "test"

    graphene_type = convert_django_field_with_choices(field)
    assert isinstance(graphene_type, graphene.Enum)
    assert graphene_type._meta.name == "TranslatedModelLanguage"
    assert graphene_type._meta.enum.__members__["ES"].value == "es"
    assert graphene_type._meta.enum.__members__["ES"].description == "Spanish"
    assert graphene_type._meta.enum.__members__["EN"].value == "en"
    assert graphene_type._meta.enum.__members__["EN"].description == "English"


def test_field_with_grouped_choices():
    field = models.CharField(
        help_text="Language",
        choices=(("Europe", (("es", "Spanish"), ("en", "English"))),),
    )

    class GroupedChoicesModel(models.Model):
        language = field

        class Meta:
            app_label = "test"

    convert_django_field_with_choices(field)


def test_field_with_choices_gettext():
    field = models.CharField(
        help_text="Language", choices=(("es", _("Spanish")), ("en", _("English")))
    )

    class TranslatedChoicesModel(models.Model):
        language = field

        class Meta:
            app_label = "test"

    convert_django_field_with_choices(field)


def test_field_with_choices_collision():
    field = models.CharField(
        help_text="Timezone",
        choices=(
            ("Etc/GMT+1+2", "Fake choice to produce double collision"),
            ("Etc/GMT+1", "Greenwich Mean Time +1"),
            ("Etc/GMT-1", "Greenwich Mean Time -1"),
        ),
    )

    class CollisionChoicesModel(models.Model):
        timezone = field

        class Meta:
            app_label = "test"

    convert_django_field_with_choices(field)


def test_should_float_convert_float():
    assert_conversion(models.FloatField, graphene.Float)


def test_should_manytomany_convert_connectionorlist():
    registry = Registry()
    dynamic_field = convert_django_field(Reporter._meta.local_many_to_many[0], registry)
    assert not dynamic_field.get_type()


def test_should_manytomany_convert_connectionorlist_list():
    class A(DjangoObjectType):
        class Meta:
            model = Reporter

    graphene_field = convert_django_field(
        Reporter._meta.local_many_to_many[0], A._meta.registry
    )
    assert isinstance(graphene_field, graphene.Dynamic)
    dynamic_field = graphene_field.get_type()
    assert isinstance(dynamic_field, graphene.Field)
    assert isinstance(dynamic_field.type, graphene.List)
    assert dynamic_field.type.of_type == A


def test_should_manytomany_convert_connectionorlist_connection():
    class A(DjangoObjectType):
        class Meta:
            model = Reporter
            interfaces = (Node,)

    graphene_field = convert_django_field(
        Reporter._meta.local_many_to_many[0], A._meta.registry
    )
    assert isinstance(graphene_field, graphene.Dynamic)
    dynamic_field = graphene_field.get_type()
    assert isinstance(dynamic_field, ConnectionField)
    assert dynamic_field.type == A._meta.connection


def test_should_manytoone_convert_connectionorlist():
    class A(DjangoObjectType):
        class Meta:
            model = Article

    graphene_field = convert_django_field(Reporter.articles.rel, 
                                          A._meta.registry)
    assert isinstance(graphene_field, graphene.Dynamic)
    dynamic_field = graphene_field.get_type()
    assert isinstance(dynamic_field, graphene.Field)
    assert isinstance(dynamic_field.type, graphene.List)
    assert dynamic_field.type.of_type == A


def test_should_onetoone_reverse_convert_model():
    class A(DjangoObjectType):
        class Meta:
            model = FilmDetails

    graphene_field = convert_django_field(Film.details.related,
                                          A._meta.registry)
    assert isinstance(graphene_field, graphene.Dynamic)
    dynamic_field = graphene_field.get_type()
    assert isinstance(dynamic_field, graphene.Field)
    assert dynamic_field.type == A


@pytest.mark.skipif(ArrayField is MissingType, reason="ArrayField should exist")
def test_should_postgres_array_convert_list():
    field = assert_conversion(
        ArrayField, graphene.List, models.CharField(max_length=100)
    )
    assert isinstance(field.type, graphene.NonNull)
    assert isinstance(field.type.of_type, graphene.List)
    assert field.type.of_type.of_type == graphene.String


@pytest.mark.skipif(ArrayField is MissingType, reason="ArrayField should exist")
def test_should_postgres_array_multiple_convert_list():
    field = assert_conversion(
        ArrayField, graphene.List, ArrayField(models.CharField(max_length=100))
    )
    assert isinstance(field.type, graphene.NonNull)
    assert isinstance(field.type.of_type, graphene.List)
    assert isinstance(field.type.of_type.of_type, graphene.List)
    assert field.type.of_type.of_type.of_type == graphene.String


@pytest.mark.skipif(HStoreField is MissingType, reason="HStoreField should exist")
def test_should_postgres_hstore_convert_string():
    assert_conversion(HStoreField, JSONString)


@pytest.mark.skipif(JSONField is MissingType, reason="JSONField should exist")
def test_should_postgres_json_convert_string():
    assert_conversion(JSONField, JSONString)


@pytest.mark.skipif(RangeField is MissingType, reason="RangeField should exist")
def test_should_postgres_range_convert_list():
    from django.contrib.postgres.fields import IntegerRangeField

    field = assert_conversion(IntegerRangeField, graphene.List)
    assert isinstance(field.type, graphene.NonNull)
    assert isinstance(field.type.of_type, graphene.List)
    assert field.type.of_type.of_type == graphene.Int
