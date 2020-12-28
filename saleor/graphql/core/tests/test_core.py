from unittest.mock import Mock, patch

import django_filters
import graphene
import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.utils import timezone
from graphene import InputField

from ....product.models import Category, Product, ProductChannelListing
from ...product import types as product_types
from ...tests.utils import get_graphql_content, get_graphql_content_from_response
from ...utils import get_database_id, requestor_is_superuser
from ...utils.filters import filter_range_field, reporting_period_to_date
from ..enums import ReportingPeriod
from ..filters import EnumFilter
from ..mutations import BaseMutation
from ..types import FilterInputObjectType
from ..utils import (
    clean_seo_fields,
    get_duplicated_values,
    snake_to_camel_case,
    validate_slug_and_generate_if_needed,
)


def test_clean_seo_fields():
    title = "lady title"
    description = "fantasy description"
    data = {"seo": {"title": title, "description": description}}
    clean_seo_fields(data)
    assert data["seo_title"] == title
    assert data["seo_description"] == description


def test_user_error_field_name_for_related_object(
    staff_api_client, permission_manage_products
):
    query = """
    mutation {
        categoryCreate(input: {name: "Test"}, parent: "123456") {
            errors {
                field
                message
            }
            category {
                id
            }
        }
    }
    """
    response = staff_api_client.post_graphql(
        query, permissions=[permission_manage_products]
    )
    content = get_graphql_content(response)
    data = content["data"]["categoryCreate"]["category"]
    assert data is None
    error = content["data"]["categoryCreate"]["errors"][0]
    assert error["field"] == "parent"


def test_get_database_id(product):
    info = Mock(
        schema=Mock(
            get_type=Mock(return_value=Mock(graphene_type=product_types.Product))
        )
    )
    node_id = graphene.Node.to_global_id("Product", product.pk)
    pk = get_database_id(info, node_id, product_types.Product)
    assert int(pk) == product.pk


def test_snake_to_camel_case():
    assert snake_to_camel_case("test_camel_case") == "testCamelCase"
    assert snake_to_camel_case("testCamel_case") == "testCamelCase"
    assert snake_to_camel_case(123) == 123


def test_reporting_period_to_date():
    now = timezone.now()
    start_date = reporting_period_to_date(ReportingPeriod.TODAY)
    assert start_date.day == now.day
    assert start_date.hour == 0
    assert start_date.minute == 0
    assert start_date.second == 0
    assert start_date.microsecond == 0

    start_date = reporting_period_to_date(ReportingPeriod.THIS_MONTH)
    assert start_date.month == now.month
    assert start_date.day == 1
    assert start_date.hour == 0
    assert start_date.minute == 0
    assert start_date.second == 0
    assert start_date.microsecond == 0


def test_require_pagination(api_client):
    query = """
    query {
        products {
            edges {
                node {
                    name
                }
            }
        }
    }
    """
    response = api_client.post_graphql(query)
    content = get_graphql_content_from_response(response)
    assert "errors" in content
    assert content["errors"][0]["message"] == (
        "You must provide a `first` or `last` value to properly paginate the "
        "`products` connection."
    )


def test_total_count_query(api_client, product, channel_USD):
    query = """
    query ($channel: String){
        products (channel: $channel){
            totalCount
        }
    }
    """
    response = api_client.post_graphql(query, {"channel": channel_USD.slug})
    content = get_graphql_content(response)
    assert content["data"]["products"]["totalCount"] == Product.objects.count()


def test_filter_input():
    class CreatedEnum(graphene.Enum):
        WEEK = "week"
        YEAR = "year"

    class TestProductFilter(django_filters.FilterSet):
        name = django_filters.CharFilter()
        created = EnumFilter(input_class=CreatedEnum, method="created_filter")

        class Meta:
            model = Product
            fields = {"product_type__id": ["exact"]}

        def created_filter(self, queryset, _, value):
            if CreatedEnum.WEEK == value:
                return queryset
            elif CreatedEnum.YEAR == value:
                return queryset
            return queryset

    class TestFilter(FilterInputObjectType):
        class Meta:
            filterset_class = TestProductFilter

    test_filter = TestFilter()
    fields = test_filter._meta.fields

    assert "product_type__id" in fields
    product_type_id = fields["product_type__id"]
    assert isinstance(product_type_id, InputField)
    assert product_type_id.type == graphene.ID

    assert "name" in fields
    name = fields["name"]
    assert isinstance(name, InputField)
    assert name.type == graphene.String

    assert "created" in fields
    created = fields["created"]
    assert isinstance(created, InputField)
    assert created.type == CreatedEnum


@patch("graphene.types.mutation.Mutation.__init_subclass_with_meta__")
@pytest.mark.parametrize(
    "should_fail,permissions_value",
    ((False, "valid"), (False, ("valid",)), (True, 123)),
)
def test_mutation_invalid_permission_in_meta(_mocked, should_fail, permissions_value):
    def _run_test():
        BaseMutation.__init_subclass_with_meta__(
            description="dummy", permissions=permissions_value
        )

    if not should_fail:
        _run_test()
        return

    with pytest.raises(ImproperlyConfigured) as exc:
        _run_test()

    assert exc.value.args[0] == "Permissions should be a tuple or a string in Meta"


@pytest.mark.parametrize(
    "cleaned_input",
    [
        {"slug": None, "name": "test"},
        {"slug": "", "name": "test"},
        {"slug": ""},
        {"slug": None},
    ],
)
def test_validate_slug_and_generate_if_needed_raises_errors(category, cleaned_input):
    with pytest.raises(ValidationError):
        validate_slug_and_generate_if_needed(category, "name", cleaned_input)


@pytest.mark.parametrize(
    "cleaned_input", [{"slug": "test-slug"}, {"slug": "test-slug", "name": "test"}]
)
def test_validate_slug_and_generate_if_needed_not_raises_errors(
    category, cleaned_input
):
    validate_slug_and_generate_if_needed(category, "name", cleaned_input)


@pytest.mark.parametrize(
    "cleaned_input",
    [
        {"slug": None, "name": "test"},
        {"slug": "", "name": "test"},
        {"slug": ""},
        {"slug": None},
        {"slug": "test-slug"},
        {"slug": "test-slug", "name": "test"},
    ],
)
def test_validate_slug_and_generate_if_needed_generate_slug(cleaned_input):
    category = Category(name="test")
    validate_slug_and_generate_if_needed(category, "name", cleaned_input)


@pytest.mark.parametrize(
    "value, count, product_indexes",
    [
        ({"lte": 50, "gte": 25}, 1, [2]),
        ({"lte": 25}, 2, [0, 1]),
        ({"lte": 10}, 1, [0]),
        ({"gte": 40}, 0, []),
    ],
)
def test_filter_range_field(value, count, product_indexes, product_list):
    qs = ProductChannelListing.objects.all().order_by("pk")
    field = "discounted_price_amount"

    result = filter_range_field(qs, field, value)

    expected_products = [qs[index] for index in product_indexes]
    assert result.count() == count
    assert list(result) == expected_products


def test_get_duplicated_values():
    values = ("a", "b", "a", 1, 1, 1, 2)

    result = get_duplicated_values(values)

    assert result == {"a", 1}


def test_requestor_is_superuser_for_staff_user(staff_user):
    result = requestor_is_superuser(staff_user)
    assert result is False


def test_requestor_is_superuser_for_superuser(superuser):
    result = requestor_is_superuser(superuser)
    assert result is True


def test_requestor_is_superuser_for_app(app):
    result = requestor_is_superuser(app)
    assert result is False


def test_requestor_is_superuser_for_anonymous_user():
    user = AnonymousUser()
    result = requestor_is_superuser(user)
    assert result is False
