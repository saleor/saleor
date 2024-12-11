import pytest

from ...models import Page, PageType


@pytest.fixture
def page_type(db, size_page_attribute, tag_page_attribute):
    page_type = PageType.objects.create(name="Test page type", slug="test-page-type")
    page_type.page_attributes.add(size_page_attribute)
    page_type.page_attributes.add(tag_page_attribute)

    return page_type


@pytest.fixture
def page_type_with_rich_text_attribute(db, rich_text_attribute_page_type):
    page_type = PageType.objects.create(name="Test page type", slug="test-page-type")
    page_type.page_attributes.add(rich_text_attribute_page_type)
    return page_type


@pytest.fixture
def page_type_list(db, tag_page_attribute):
    page_types = list(
        PageType.objects.bulk_create(
            [
                PageType(name="Test page type 1", slug="test-page-type-1"),
                PageType(name="Example page type 2", slug="page-type-2"),
                PageType(name="Example page type 3", slug="page-type-3"),
            ]
        )
    )

    for i, page_type in enumerate(page_types):
        page_type.page_attributes.add(tag_page_attribute)
        Page.objects.create(
            title=f"Test page {i}",
            slug=f"test-url-{i}",
            is_published=True,
            page_type=page_type,
        )

    return page_types
