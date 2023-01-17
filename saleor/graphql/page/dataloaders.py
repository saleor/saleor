from collections import defaultdict

from promise import Promise

from ...attribute.models import (
    AssignedPageAttribute,
    AssignedPageAttributeValue,
    AttributePage,
)
from ...core.permissions import PagePermissions
from ...page.models import Page, PageType
from ..attribute.dataloaders import AttributesByAttributeId, AttributeValueByIdLoader
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


class AttributePagesByPageTypeIdLoader(DataLoader):
    """Loads AttributePage objects by page type ID."""

    context_key = "attributepages_by_pagetype"

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
        attribute_pages = qs.filter(page_type_id__in=keys)
        pagetype_to_attributepages = defaultdict(list)
        for attribute_page in attribute_pages:
            pagetype_to_attributepages[attribute_page.page_type_id].append(
                attribute_page
            )
        return [pagetype_to_attributepages[key] for key in keys]


class AssignedPageAttributesByPageIdLoader(DataLoader):
    context_key = "assignedpageattributes_by_page"

    def batch_load(self, keys):
        requestor = get_user_or_app_from_context(self.context)
        if (
            requestor
            and requestor.is_active
            and requestor.has_perm(PagePermissions.MANAGE_PAGES)
        ):
            qs = AssignedPageAttribute.objects.using(
                self.database_connection_name
            ).all()
        else:
            qs = AssignedPageAttribute.objects.using(
                self.database_connection_name
            ).filter(assignment__attribute__visible_in_storefront=True)
        assigned_page_attributes = qs.filter(page_id__in=keys)
        page_to_assignedattributes = defaultdict(list)
        for assigned_page_attribute in assigned_page_attributes:
            page_to_assignedattributes[assigned_page_attribute.page_id].append(
                assigned_page_attribute
            )
        return [page_to_assignedattributes[page_id] for page_id in keys]


class AttributeValuesByAssignedPageAttributeIdLoader(DataLoader):
    context_key = "attributevalues_by_assigned_pageattribute"

    def batch_load(self, keys):
        attribute_values = AssignedPageAttributeValue.objects.using(
            self.database_connection_name
        ).filter(assignment_id__in=keys)
        value_ids = [a.value_id for a in attribute_values]

        def map_assignment_to_values(values):
            value_map = dict(zip(value_ids, values))
            assigned_page_map = defaultdict(list)
            for attribute_value in attribute_values:
                assigned_page_map[attribute_value.assignment_id].append(
                    value_map.get(attribute_value.value_id)
                )
            return [assigned_page_map[key] for key in keys]

        return (
            AttributeValueByIdLoader(self.context)
            .load_many(value_ids)
            .then(map_assignment_to_values)
        )


class SelectedAttributesByPageIdLoader(DataLoader):
    context_key = "selectedattributes_by_page"

    def batch_load(self, keys):
        def with_pages_and_assigned_attributes(result):
            pages, page_attributes = result
            assigned_page_attributes_ids = list(
                {attr.id for attrs in page_attributes for attr in attrs}
            )
            page_type_ids = [page.page_type_id for page in pages]
            page_attributes = dict(zip(keys, page_attributes))

            def with_attribute_pages_and_values(result):
                attribute_pages, attribute_values = result
                attribute_ids = list(
                    {ap.attribute_id for aps in attribute_pages for ap in aps}
                )
                attribute_pages = dict(zip(page_type_ids, attribute_pages))
                attribute_values = dict(
                    zip(assigned_page_attributes_ids, attribute_values)
                )

                def with_attributes(attributes):
                    id_to_attribute = dict(zip(attribute_ids, attributes))
                    selected_attributes_map = defaultdict(list)
                    for key, page in zip(keys, pages):
                        assigned_pagetype_attributes = attribute_pages[
                            page.page_type_id
                        ]
                        assigned_page_attributes = page_attributes[key]
                        for assigned_pagetype_attribute in assigned_pagetype_attributes:
                            page_assignment = next(
                                (
                                    apa
                                    for apa in assigned_page_attributes
                                    if apa.assignment_id
                                    == assigned_pagetype_attribute.id
                                ),
                                None,
                            )
                            attribute = id_to_attribute[
                                assigned_pagetype_attribute.attribute_id
                            ]
                            if page_assignment:
                                values = attribute_values[page_assignment.id]
                            else:
                                values = []
                            selected_attributes_map[key].append(
                                {"values": values, "attribute": attribute}
                            )
                    return [selected_attributes_map[key] for key in keys]

                return (
                    AttributesByAttributeId(self.context)
                    .load_many(attribute_ids)
                    .then(with_attributes)
                )

            attribute_pages = AttributePagesByPageTypeIdLoader(self.context).load_many(
                page_type_ids
            )
            attribute_values = AttributeValuesByAssignedPageAttributeIdLoader(
                self.context
            ).load_many(assigned_page_attributes_ids)
            return Promise.all([attribute_pages, attribute_values]).then(
                with_attribute_pages_and_values
            )

        pages = PageByIdLoader(self.context).load_many(keys)
        assigned_attributes = AssignedPageAttributesByPageIdLoader(
            self.context
        ).load_many(keys)

        return Promise.all([pages, assigned_attributes]).then(
            with_pages_and_assigned_attributes
        )
