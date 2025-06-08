from collections import defaultdict
from collections.abc import Iterable

from promise import Promise

from ...attribute.models import AssignedPageAttributeValue, Attribute, AttributePage
from ...page.models import Page, PageType
from ..attribute.dataloaders import (
    AttributesByAttributeId,
    AttributesBySlugLoader,
    AttributeValueByIdLoader,
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


class BaseAttributeValuesByPageIdLoader(DataLoader[int, list[dict]]):
    def get_page_attributes_dataloader(self):
        raise NotImplementedError()

    def batch_load(self, keys):
        # Using list + iterator is a small optimisation because iterator causes
        # the db to not store the whole resultset into the memory
        # https://docs.djangoproject.com/en/3.2/ref/models/querysets/#iterator
        attribute_values = list(
            AssignedPageAttributeValue.objects.using(self.database_connection_name)
            .filter(page_id__in=keys)
            .iterator(chunk_size=1000)
        )
        value_ids = [a.value_id for a in attribute_values]

        def with_pages(pages):
            pages = [page for page in pages if page]
            page_type_ids = [p.page_type_id for p in pages]

            def with_attributes_and_values(result):
                attribute_pages, values = result
                page_type_attrubutes = dict(
                    zip(page_type_ids, attribute_pages, strict=False)
                )
                values_by_id_map = dict(zip(value_ids, values, strict=False))
                assigned_page_map = defaultdict(list)

                for page in pages:
                    page_values = [
                        values_by_id_map.get(page_value.value_id)
                        for page_value in attribute_values
                        if page_value.page_id == page.id
                    ]

                    attributes = page_type_attrubutes[page.page_type_id]
                    for attribute_tuple in attributes:
                        attribute = attribute_tuple
                        values = [
                            value
                            for value in page_values
                            if value and value.attribute_id == attribute.id
                        ]
                        assigned_page_map[page.id].append(
                            {
                                "attribute": attribute,
                                "values": values,
                            }
                        )
                return [assigned_page_map[key] for key in keys]

            attributes = self.get_page_attributes_dataloader().load_many(page_type_ids)
            values = AttributeValueByIdLoader(self.context).load_many(value_ids)
            return Promise.all([attributes, values]).then(with_attributes_and_values)

        return PageByIdLoader(self.context).load_many(keys).then(with_pages)


class AttributeValuesAllByPageIdLoader(BaseAttributeValuesByPageIdLoader):
    context_key = "attributevalues_all_by_page"

    def get_page_attributes_dataloader(self):
        return PageAttributesAllByPageTypeIdLoader(self.context)


class AttributeValuesVisibleInStorefrontByPageIdLoader(
    BaseAttributeValuesByPageIdLoader
):
    context_key = "attributevalues_visible_in_storefront_by_page"

    def get_page_attributes_dataloader(self):
        return PageAttributesVisibleInStorefrontByPageTypeIdLoader(self.context)


class SelectedAttributesAllByPageIdLoader(DataLoader[int, list[dict]]):
    context_key = "selectedattributes_all_by_page"

    def batch_load(self, page_ids):
        return AttributeValuesAllByPageIdLoader(self.context).load_many(page_ids)


class SelectedAttributesVisibleInStorefrontPageIdLoader(DataLoader[int, list[dict]]):
    context_key = "selectedattributes_visible_in_storefront_by_page"

    def batch_load(self, page_ids):
        return AttributeValuesVisibleInStorefrontByPageIdLoader(self.context).load_many(
            page_ids
        )


class BasePageAttributeByPageTypeIdAndAttributeSlugLoader(
    DataLoader[PageTypeIdAndAttributeSlug, Attribute]
):
    """Loads page attributes by page type ID and attribute slug."""

    context_key = "page_attributes_by_pagetype_and_attributeslug"

    @staticmethod
    def filter_attributes(attributes: list[Attribute]) -> list[Attribute]:
        """Filter attributes based on custom logic, if needed."""
        return attributes

    def batch_load(self, keys: Iterable[PageTypeIdAndAttributeSlug]):
        slugs = [slug for _, slug in keys]

        def with_attributes(attributes):
            attributes = self.filter_attributes(attributes)
            attribute_ids = [attr.id for attr in attributes if attr]
            page_attributes_pairs = (
                AttributePage.objects.using(self.database_connection_name)
                .filter(
                    page_type_id__in=[page_type_id for page_type_id, _ in keys],
                    attribute_id__in=attribute_ids,
                )
                .values_list("page_type_id", "attribute_id")
            )

            attribute_slug_map = {
                attr.id: attr.slug for attr in attributes if attr.slug in slugs
            }
            attributes_map = {attr.id: attr for attr in attributes}
            page_type_to_attributes_map = {}
            for page_type_id, attr_id in page_attributes_pairs:
                page_type_to_attributes_map[
                    (page_type_id, attribute_slug_map.get(attr_id))
                ] = attributes_map.get(attr_id)
            return [
                page_type_to_attributes_map.get((page_type_id, slug))
                for page_type_id, slug in keys
            ]

        return (
            AttributesBySlugLoader(self.context).load_many(slugs).then(with_attributes)
        )


class PageAttributeByPageTypeIdAndAttributeSlugLoader(
    BasePageAttributeByPageTypeIdAndAttributeSlugLoader
):
    """Loads page attributes by page type ID and attribute slug."""

    context_key = "page_attribute_by_pagetype_and_attributeslug"


class PageAttributeVisibleInStorefrontByPageTypeIdAndAttributeSlugLoader(
    BasePageAttributeByPageTypeIdAndAttributeSlugLoader
):
    """Loads page attributes by page type ID and attribute slug."""

    context_key = "page_attributes_visible_in_storefront_by_pagetype_and_attributeslug"

    @staticmethod
    def filter_attributes(attributes: list[Attribute]) -> list[Attribute]:
        return [attr for attr in attributes if attr and attr.visible_in_storefront]


class BaseAttributeValuesByPageIdAndAttributeSlugLoader(
    DataLoader[PageTypeIdAndAttributeSlug, dict]
):
    def get_page_attributes_dataloader(self):
        raise NotImplementedError()

    def batch_load(self, keys: Iterable[PageTypeIdAndAttributeSlug]):
        # Using list + iterator is a small optimisation because iterator causes
        # the db to not store the whole resultset into the memory
        # https://docs.djangoproject.com/en/3.2/ref/models/querysets/#iterator
        page_ids = [page_id for page_id, _ in keys]
        slugs = [slug for _, slug in keys]
        attribute_values = list(
            AssignedPageAttributeValue.objects.using(self.database_connection_name)
            .filter(page_id__in=page_ids)
            .iterator()
        )
        value_ids = [a.value_id for a in attribute_values]

        def with_pages(pages):
            pages = [page for page in pages if page]
            page_type_ids = [p.page_type_id for p in pages]

            def with_attributes_and_values(result):
                attribute_pages, values = result
                page_type_attribute = dict(
                    zip(page_type_ids, attribute_pages, strict=False)
                )
                values_by_id_map = dict(zip(value_ids, values, strict=False))
                assigned_page_map = {}

                for page in pages:
                    page_values = [
                        values_by_id_map.get(page_value.value_id)
                        for page_value in attribute_values
                        if page_value.page_id == page.id
                    ]

                    attribute = page_type_attribute[page.page_type_id]
                    if attribute:
                        values = [
                            value
                            for value in page_values
                            if value and value.attribute_id == attribute.id
                        ]
                        assigned_page_map[(page.id, attribute.slug)] = {
                            "attribute": attribute,
                            "values": values,
                        }
                return [assigned_page_map.get(key) for key in keys]

            attributes = self.get_page_attributes_dataloader().load_many(
                list(zip(page_type_ids, slugs, strict=False))
            )
            values = AttributeValueByIdLoader(self.context).load_many(value_ids)
            return Promise.all([attributes, values]).then(with_attributes_and_values)

        return PageByIdLoader(self.context).load_many(page_ids).then(with_pages)


class AttributeValuesAllByPageIdAndAttributeSlugLoader(
    BaseAttributeValuesByPageIdAndAttributeSlugLoader
):
    context_key = "attributevalues_all_by_page_and_attributeslug"

    def get_page_attributes_dataloader(self):
        return PageAttributeByPageTypeIdAndAttributeSlugLoader(self.context)


class AttributeValuesVisibleInStorefrontByPageIdAndAttributeSlugLoader(
    BaseAttributeValuesByPageIdAndAttributeSlugLoader
):
    context_key = "attributevalues_visible_in_storefront_by_page_and_attributeslug"

    def get_page_attributes_dataloader(self):
        return PageAttributeVisibleInStorefrontByPageTypeIdAndAttributeSlugLoader(
            self.context
        )


class SelectedAttributeAllByPageIdAttributeSlugLoader(DataLoader[int, list[dict]]):
    context_key = "selectedattributes_all_by_page_and_attribute_slug"

    def batch_load(self, page_ids):
        return AttributeValuesAllByPageIdAndAttributeSlugLoader(self.context).load_many(
            page_ids
        )


class SelectedAttributeVisibleInStorefrontPageIdAttributeSlugLoader(
    DataLoader[int, list[dict]]
):
    context_key = "selectedattributes_visible_in_storefront_by_page_and_attribute_slug"

    def batch_load(self, page_ids):
        return AttributeValuesVisibleInStorefrontByPageIdAndAttributeSlugLoader(
            self.context
        ).load_many(page_ids)
