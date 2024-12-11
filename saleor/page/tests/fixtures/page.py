import pytest

from ....attribute.utils import associate_attribute_values_to_instance
from ....tests.utils import dummy_editorjs
from ...models import Page


@pytest.fixture
def page(db, page_type, size_page_attribute):
    data = {
        "slug": "test-url",
        "title": "Test page",
        "content": dummy_editorjs("Test content."),
        "is_published": True,
        "page_type": page_type,
    }
    page = Page.objects.create(**data)

    # associate attribute value
    page_attr_value = size_page_attribute.values.get(slug="10")
    associate_attribute_values_to_instance(
        page, {size_page_attribute.pk: [page_attr_value]}
    )

    return page


@pytest.fixture
def page_with_rich_text_attribute(
    db, page_type_with_rich_text_attribute, rich_text_attribute_page_type
):
    data = {
        "slug": "test-url",
        "title": "Test page",
        "content": dummy_editorjs("Test content."),
        "is_published": True,
        "page_type": page_type_with_rich_text_attribute,
    }
    page = Page.objects.create(**data)

    # associate attribute value
    page_attr = page_type_with_rich_text_attribute.page_attributes.first()
    page_attr_value = page_attr.values.first()

    associate_attribute_values_to_instance(page, {page_attr.pk: [page_attr_value]})

    return page


@pytest.fixture
def page_list(db, page_type):
    data_1 = {
        "slug": "test-url-1",
        "title": "Test page",
        "content": dummy_editorjs("Test content."),
        "is_published": True,
        "page_type": page_type,
    }
    data_2 = {
        "slug": "test-url-2",
        "title": "Test page",
        "content": dummy_editorjs("Test content."),
        "is_published": True,
        "page_type": page_type,
    }
    pages = Page.objects.bulk_create([Page(**data_1), Page(**data_2)])
    return pages


@pytest.fixture
def page_list_unpublished(db, page_type):
    pages = Page.objects.bulk_create(
        [
            Page(
                slug="page-1", title="Page 1", is_published=False, page_type=page_type
            ),
            Page(
                slug="page-2", title="Page 2", is_published=False, page_type=page_type
            ),
            Page(
                slug="page-3", title="Page 3", is_published=False, page_type=page_type
            ),
        ]
    )
    return pages
