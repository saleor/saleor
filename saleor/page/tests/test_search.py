import pytest

from ...attribute.models import AttributeValue
from ...attribute.utils import associate_attribute_values_to_instance
from ..models import Page
from ..search import (
    update_pages_search_vector,
)


def test_update_pages_search_vector_multiple_pages(page_list):
    """Test updating search vector for multiple pages."""
    # given
    assert all(page.search_index_dirty for page in page_list)

    # when
    update_pages_search_vector(page_list)

    # then
    for page in page_list:
        page.refresh_from_db()
        assert page.search_vector is not None
        assert page.search_index_dirty is False


def test_update_pages_search_vector_empty_list(db):
    """Test updating search vector with empty page IDs list."""
    # given
    pages = []

    # when/then - should not raise any errors
    update_pages_search_vector(pages)


@pytest.fixture
def page_list_with_attributes(
    page_type_list,
    size_page_attribute,
    tag_page_attribute,
    page_type_product_reference_attribute,
    product_list,
):
    for page_type in page_type_list:
        page_type.page_attributes.add(
            page_type_product_reference_attribute,
            size_page_attribute,
            tag_page_attribute,
        )

    product_1, product_2, product_3 = product_list
    attribute_values = AttributeValue.objects.bulk_create(
        [
            AttributeValue(
                attribute=page_type_product_reference_attribute,
                name=f"Product {product_1.pk}",
                slug=f"product-{product_1.pk}",
                reference_product=product_1,
            ),
            AttributeValue(
                attribute=page_type_product_reference_attribute,
                name=f"Product {product_2.pk}",
                slug=f"product-{product_2.pk}",
                reference_product=product_2,
            ),
            AttributeValue(
                attribute=page_type_product_reference_attribute,
                name=f"Product {product_3.pk}",
                slug=f"product-{product_3.pk}",
                reference_product=product_3,
            ),
        ]
    )

    page_list = list(Page.objects.all())
    size_attribute_value = size_page_attribute.values.first()
    tag_attribute_value = tag_page_attribute.values.first()
    for i, page in enumerate(page_list):
        associate_attribute_values_to_instance(
            page,
            {
                page_type_product_reference_attribute.pk: [attribute_values[i]],
                size_page_attribute.pk: [size_attribute_value],
                tag_page_attribute.pk: [tag_attribute_value],
            },
        )
    return page_list


def test_update_pages_search_vector_constant_queries(
    page_list_with_attributes, django_assert_num_queries
):
    """Ensure that data loaders are working correctly and number of db queries is constant."""
    # given
    page_list = page_list_with_attributes

    # when & then
    # Expected query breakdown (10 total):
    # 1. Load page types (1 query)
    # 2. Load page data for select_for_update (1 query)
    # 3. Load page-attribute relationships (1 query)
    # 4. Load attributes (1 query)
    # 5. Load attribute value assignments - batched (1 query)
    # 6. Load attribute values - batched (1 query)
    # 7. Load reference page titles (1 query)
    # 8. Transaction savepoint (1 query)
    # 9. Bulk update (1 query)
    # 10. Release savepoint (1 query)

    expected_queries = 10
    with django_assert_num_queries(expected_queries):  # Expected number of queries
        update_pages_search_vector(page_list[: len(page_list) - 1])
    with django_assert_num_queries(
        expected_queries
    ):  # Same number of queries for more pages
        update_pages_search_vector(page_list)
