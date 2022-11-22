import enum
import os
from unittest.mock import patch

import django_filters
import graphene
import pytest
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.utils import timezone
from graphene import InputField
from micawber import ProviderException, ProviderRegistry

from ....core.utils.validators import get_oembed_data
from ....product import ProductMediaTypes
from ....product.models import Product, ProductChannelListing
from ...tests.utils import get_graphql_content, get_graphql_content_from_response
from ...utils import requestor_is_superuser
from ...utils.filters import filter_range_field, reporting_period_to_date
from ..enums import ReportingPeriod
from ..filters import EnumFilter
from ..mutations import BaseMutation
from ..types import FilterInputObjectType
from ..utils import add_hash_to_file_name, get_duplicated_values, snake_to_camel_case
from . import ErrorTest


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


def test_require_pagination(api_client, channel_USD):
    query = """
    query GetProducts($channel: String) {
        products(channel: $channel) {
            edges {
                node {
                    name
                }
            }
        }
    }
    """
    response = api_client.post_graphql(query, {"channel": channel_USD.slug})
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


class PermissionEnumForTests(enum.Enum):
    TEST = "test"


@patch("graphene.types.mutation.Mutation.__init_subclass_with_meta__")
@pytest.mark.parametrize(
    "should_fail,permissions_value",
    (
        (False, (PermissionEnumForTests.TEST,)),
        (True, PermissionEnumForTests.TEST),
        (True, 123),
        (True, ("TEST",)),
    ),
)
def test_mutation_invalid_permission_in_meta(_mocked, should_fail, permissions_value):
    def _run_test():
        BaseMutation.__init_subclass_with_meta__(
            description="dummy",
            error_type_class=ErrorTest,
            permissions=permissions_value,
        )

    if not should_fail:
        _run_test()
        return

    with pytest.raises(ImproperlyConfigured):
        _run_test()


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


def test_filter_products_with_zero_discount(product_list):
    product_list[0].channel_listings.update(discounted_price_amount=0)
    qs = ProductChannelListing.objects.all().order_by("pk")
    field = "discounted_price_amount"

    result = filter_range_field(qs, field, {"lte": 0, "gte": 0})

    expected_products = list(qs.filter(product=product_list[0]))
    assert result.count() == 1
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


@pytest.mark.vcr
@pytest.mark.parametrize(
    "url, expected_media_type",
    [
        (
            "http://www.youtube.com/watch?v=dQw4w9WgXcQ",
            ProductMediaTypes.VIDEO,
        ),
        (
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            ProductMediaTypes.VIDEO,
        ),
        (
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&ab_channel=TestingChannel",
            ProductMediaTypes.VIDEO,
        ),
        (
            "https://vimeo.com/148751763",
            ProductMediaTypes.VIDEO,
        ),
        (
            "https://www.flickr.com/photos/megane_wakui/31740618232/",
            ProductMediaTypes.IMAGE,
        ),
    ],
)
def test_get_oembed_data(url, expected_media_type):
    oembed_data, media_type = get_oembed_data(url, "media_url")

    assert oembed_data is not {}
    assert media_type == expected_media_type


@pytest.mark.parametrize(
    "url",
    [
        "https://www.streamable.com/8vnouo",
        "https://www.flickr.com/photos/test/test/",
        "https://www.youtube.com/embed/v=dQw4w9WgXcQ",
        "https://vimeo.com/test",
        "http://onet.pl/",
    ],
)
@patch.object(ProviderRegistry, "request")
def test_get_oembed_data_unsupported_media_provider(mocked_provider, url):
    mocked_provider.side_effect = ProviderException()
    with pytest.raises(
        ValidationError, match="Unsupported media provider or incorrect URL."
    ):
        get_oembed_data(url, "media_url")


def test_add_hash_to_file_name(image, media_root):
    previous_file_name = image._name

    add_hash_to_file_name(image)

    assert previous_file_name != image._name
    file_name, format = os.path.splitext(image._name)
    assert image._name.startswith(file_name)
    assert image._name.endswith(format)
