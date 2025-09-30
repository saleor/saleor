from collections import defaultdict

from ...attribute.models import Attribute, AttributePage
from ...page.models import Page, PageType
from ..attribute.dataloaders.attributes import (
    AttributesByAttributeId,
)
from ..core.dataloaders import DataLoader

PageTypeIdAndAttributeSlug = tuple[int, str]


class PageByIdLoader(DataLoader[int, Page]):
    context_key = "page_by_id"

    def batch_load(self, keys):
        pages = Page.objects.using(self.database_connection_name).in_bulk(keys)
        return [pages.get(page_id) for page_id in keys]


class PageTypeByIdLoader(DataLoader[int, PageType]):
    context_key = "page_type_by_id"

    def batch_load(self, keys):
        page_types = PageType.objects.using(self.database_connection_name).in_bulk(keys)
        return [page_types.get(page_type_id) for page_type_id in keys]


class PagesByPageTypeIdLoader(DataLoader[int, list[Page]]):
    """Loads pages by pages type ID."""

    context_key = "pages_by_pagetype"

    def batch_load(self, keys):
        pages = Page.objects.using(self.database_connection_name).filter(
            page_type_id__in=keys
        )

        pagetype_to_pages = defaultdict(list)
        for page in pages:
            pagetype_to_pages[page.page_type_id].append(page)

        return [pagetype_to_pages[key] for key in keys]


class BasePageAttributesByPageTypeIdLoader(DataLoader[int, list[Attribute]]):
    """Loads page attributes by page type ID."""

    context_key = "page_attributes_by_pagetype"

    @staticmethod
    def filter_attributes(attributes: list[Attribute]) -> list[Attribute]:
        """Filter attributes based on custom logic, if needed."""
        return attributes

    def batch_load(self, keys):
        page_type_attribute_pairs = (
            AttributePage.objects.using(self.database_connection_name)
            .filter(page_type_id__in=keys)
            .values_list("page_type_id", "attribute_id")
        )
        attribute_ids = {attr_id for _, attr_id in page_type_attribute_pairs}

        def map_attributes(attributes):
            attributes = self.filter_attributes(attributes)
            attributes_map = {attr.id: attr for attr in attributes}
            page_type_to_attributes_map = defaultdict(list)
            for page_type_id, attr_id in page_type_attribute_pairs:
                if attr_id in attributes_map:
                    # Only add attributes that are in the attributes_map to ensure
                    # that filtered attributes are respected.
                    page_type_to_attributes_map[page_type_id].append(
                        attributes_map.get(attr_id)
                    )
            return [
                page_type_to_attributes_map.get(page_type_id, [])
                for page_type_id in keys
            ]

        return (
            AttributesByAttributeId(self.context)
            .load_many(attribute_ids)
            .then(map_attributes)
        )


class PageAttributesAllByPageTypeIdLoader(BasePageAttributesByPageTypeIdLoader):
    """Loads page attributes by page type ID."""

    context_key = "page_attributes_all_by_pagetype"


class PageAttributesVisibleInStorefrontByPageTypeIdLoader(
    BasePageAttributesByPageTypeIdLoader
):
    """Loads page attributes by page type ID."""

    context_key = "page_attributes_visible_in_storefront_by_pagetype"

    @staticmethod
    def filter_attributes(attributes: list[Attribute]) -> list[Attribute]:
        return [attr for attr in attributes if attr and attr.visible_in_storefront]
