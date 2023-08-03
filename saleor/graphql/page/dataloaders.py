from collections import defaultdict

from django.db.models import prefetch_related_objects

from ...attribute.models import AssignedPageAttributeValue, AttributePage
from ...page.models import Page, PageType
from ...permission.enums import PagePermissions
from ..attribute.dataloaders import AttributesByAttributeId
from ..core.dataloaders import DataLoader
from ..utils import get_user_or_app_from_context


class PageByIdLoader(DataLoader):
    context_key = "page_by_id"

    def batch_load(self, keys):
        pages = Page.objects.using(self.database_connection_name).in_bulk(keys)
        return [pages.get(page_id) for page_id in keys]


class PageTypeByIdLoader(DataLoader):
    context_key = "page_type_by_id"

    def batch_load(self, keys):
        page_types = PageType.objects.using(self.database_connection_name).in_bulk(keys)
        return [page_types.get(page_type_id) for page_type_id in keys]


class PagesByPageTypeIdLoader(DataLoader):
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


class PageAttributesByPageTypeIdLoader(DataLoader):
    """Loads page attributes by page type ID."""

    context_key = "page_attributes_by_pagetype"

    def batch_load(self, keys):
        requestor = get_user_or_app_from_context(self.context)
        if (
            requestor
            and requestor.is_active
            and requestor.has_perm(PagePermissions.MANAGE_PAGES)
        ):
            qs = AttributePage.objects.using(self.database_connection_name).all()
        else:
            qs = AttributePage.objects.using(self.database_connection_name).filter(
                attribute__visible_in_storefront=True
            )

        page_type_attribute_pairs = qs.filter(page_type_id__in=keys).values_list(
            "page_type_id", "attribute_id"
        )

        page_type_to_attributes_map = defaultdict(list)
        for page_type_id, attr_id in page_type_attribute_pairs:
            page_type_to_attributes_map[page_type_id].append(attr_id)

        def map_attributes(attributes):
            attributes_map = {attr.id: attr for attr in attributes}
            return [
                [
                    attributes_map[attr_id]
                    for attr_id in page_type_to_attributes_map[page_type_id]
                ]
                for page_type_id in keys
            ]

        return (
            AttributesByAttributeId(self.context)
            .load_many(set(attr_id for _, attr_id in page_type_attribute_pairs))
            .then(map_attributes)
        )


class AttributeValuesByPageIdLoader(DataLoader):
    context_key = "attributevalues_by_page"

    def batch_load(self, keys):
        # Using list + iterator is a small optimisation because iterator causes
        # the db to not store the whole resultset into the memory
        # https://docs.djangoproject.com/en/3.2/ref/models/querysets/#iterator
        attribute_values = list(
            AssignedPageAttributeValue.objects.using(self.database_connection_name)
            .filter(page_id__in=keys)
            .iterator()
        )
        prefetch_related_objects(attribute_values, "value")

        def with_pages(pages):
            pages = [page for page in pages if page]
            page_type_ids = [p.page_type_id for p in pages]

            def with_attributes(attribute_pages):
                page_type_attrubutes = dict(zip(page_type_ids, attribute_pages))
                assigned_page_map = defaultdict(list)

                for page in pages:
                    page_values = [
                        page_value.value
                        for page_value in attribute_values
                        if page_value.page_id == page.id
                    ]

                    attributes = page_type_attrubutes[page.page_type_id]
                    for attribute_tuple in attributes:
                        attribute = attribute_tuple
                        values = [
                            value
                            for value in page_values
                            if value.attribute_id == attribute.id
                        ]
                        assigned_page_map[page.id].append(
                            {
                                "attribute": attribute,
                                "values": values,
                            }
                        )
                return [assigned_page_map[key] for key in keys]

            return (
                PageAttributesByPageTypeIdLoader(self.context)
                .load_many(page_type_ids)
                .then(with_attributes)
            )

        return PageByIdLoader(self.context).load_many(keys).then(with_pages)


class SelectedAttributesByPageIdLoader(DataLoader):
    context_key = "selectedattributes_by_page"

    def batch_load(self, page_ids):
        return AttributeValuesByPageIdLoader(self.context).load_many(page_ids)
