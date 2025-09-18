from collections import defaultdict
from collections.abc import Iterable

from django.db.models import F, Window
from django.db.models.functions import RowNumber
from django.db.models.query import QuerySet
from promise import Promise

from ....attribute.models import Attribute, AttributeValue
from ....attribute.models.page import AssignedPageAttributeValue, AttributePage
from ....attribute.models.product import AssignedProductAttributeValue, AttributeProduct
from ....attribute.models.product_variant import (
    AssignedVariantAttribute,
    AssignedVariantAttributeValue,
    AttributeVariant,
)
from ....core.db.connection import allow_writer_in_context
from ....page import models as page_models
from ....product import models as product_models
from ...core.dataloaders import DataLoader
from ...page.dataloaders import PageByIdLoader
from ...product.dataloaders.products import ProductByIdLoader, ProductByVariantIdLoader
from .attributes import (
    AttributesByAttributeId,
    AttributesBySlugLoader,
    AttributeValueByIdLoader,
)

type PRODUCT_ID = int
type PRODUCT_TYPE_ID = int
type PAGE_ID = int
type VARIANT_ID = int
type ATTRIBUTE_ID = int
type ATTRIBUTE_SLUG = str
type LIMIT = int | None
type VARIANT_SELECTION = bool | None


class AttributesByProductIdAndLimitLoader(
    DataLoader[tuple[PRODUCT_ID, LIMIT], list[Attribute]]
):
    context_key = "attribute_ids_by_product_id_and_limit"

    def get_attribute_product_qs(
        self, product_type_ids: set[int]
    ) -> QuerySet[AttributeProduct]:
        return AttributeProduct.objects.using(self.database_connection_name).filter(
            product_type__in=product_type_ids
        )

    def batch_load(self, keys: Iterable[tuple[PRODUCT_ID, LIMIT]]):
        @allow_writer_in_context(self.context)
        def with_products(products: list[product_models.Product]):
            product_id_to_product_type_id_map = {
                product.id: product.product_type_id for product in products if product
            }
            product_type_ids = set(product_id_to_product_type_id_map.values())

            attribute_products = (
                self.get_attribute_product_qs(product_type_ids)
                .using(self.database_connection_name)
                .values_list("attribute_id", "product_type_id")
            )

            product_type_id_to_attribute_ids = defaultdict(list)

            for attribute_id, attr_product_type_id in attribute_products:
                product_type_id_to_attribute_ids[attr_product_type_id].append(
                    attribute_id
                )

            attribute_ids = set()
            for product_id, limit in keys:
                product_type_id = product_id_to_product_type_id_map.get(product_id)
                if not product_type_id:
                    continue
                attribute_ids.update(
                    product_type_id_to_attribute_ids.get(product_type_id, [])[:limit]
                )

            def get_attributes_for_products(attributes: list[Attribute]):
                attribute_map = {attr.id: attr for attr in attributes}

                response = []
                for product_id, limit in keys:
                    single_response_entry: list[Attribute] = []
                    product_type_id = product_id_to_product_type_id_map.get(product_id)
                    if not product_type_id:
                        response.append(single_response_entry)
                        continue
                    product_attribute_ids = product_type_id_to_attribute_ids.get(
                        product_type_id, []
                    )[:limit]
                    for product_attribute_id in product_attribute_ids:
                        attribute = attribute_map.get(product_attribute_id)
                        if not attribute:
                            continue
                        single_response_entry.append(attribute)
                    response.append(single_response_entry)
                return response

            return (
                AttributesByAttributeId(self.context)
                .load_many(attribute_ids)
                .then(get_attributes_for_products)
            )

        product_ids = [product_id for product_id, _ in keys]
        return (
            ProductByIdLoader(self.context).load_many(product_ids).then(with_products)
        )


class AttributesVisibleToCustomerByProductIdAndLimitLoader(
    AttributesByProductIdAndLimitLoader
):
    context_key = "attributes_visible_to_customer_by_product_id_and_limit"

    def get_attribute_product_qs(
        self, product_type_ids: set[int]
    ) -> QuerySet[AttributeProduct]:
        return AttributeProduct.objects.using(self.database_connection_name).filter(
            attribute__visible_in_storefront=True,
            product_type__in=product_type_ids,
        )


class AttributeByProductIdAndAttributeSlugLoader(
    DataLoader[tuple[PRODUCT_ID, ATTRIBUTE_SLUG], Attribute | None]
):
    context_key = "attribute_by_product_id_and_attribute_slug"

    def batch_load(self, keys: Iterable[tuple[PRODUCT_ID, ATTRIBUTE_SLUG]]):
        product_ids = [product_id for product_id, _ in keys]
        attribute_slugs = [attribute_slug for _, attribute_slug in keys]

        def with_attributes_and_products(
            data: tuple[list[product_models.Product], list[Attribute]],
        ):
            products, attributes = data
            product_type_ids = {
                product.product_type_id for product in products if product is not None
            }
            product_map = {
                product.id: product for product in products if product is not None
            }
            attribute_map = {attr.slug: attr for attr in attributes if attr is not None}
            attribute_products = (
                AttributeProduct.objects.using(self.database_connection_name)
                .filter(
                    attribute__in=[attr.id for attr in attribute_map.values()],
                    product_type__in=product_type_ids,
                )
                .values_list("attribute_id", "product_type_id")
            )

            product_type_id_to_attribute_ids = defaultdict(set)
            for attribute_id, product_type_id in attribute_products:
                product_type_id_to_attribute_ids[product_type_id].add(attribute_id)

            response: list[Attribute | None] = []
            for product_id, attribute_slug in keys:
                attribute = attribute_map.get(attribute_slug)
                if not attribute:
                    response.append(None)
                    continue

                product = product_map.get(product_id)
                if not product:
                    response.append(None)
                    continue
                product_type_id = product.product_type_id
                attributes_assigned_to_product_type = (
                    product_type_id_to_attribute_ids.get(product_type_id, set())
                )
                if attribute.id in attributes_assigned_to_product_type:
                    response.append(attribute)
                else:
                    response.append(None)
            return response

        products_loader = ProductByIdLoader(self.context).load_many(product_ids)
        attributes_loader = AttributesBySlugLoader(self.context).load_many(
            attribute_slugs
        )
        return Promise.all([products_loader, attributes_loader]).then(
            with_attributes_and_products
        )


class AttributeByProductVariantIdAndAttributeSlugLoader(
    DataLoader[tuple[VARIANT_ID, ATTRIBUTE_SLUG], Attribute | None]
):
    context_key = "attribute_by_product_variant_id_and_attribute_slug"

    def batch_load(self, keys: Iterable[tuple[VARIANT_ID, ATTRIBUTE_SLUG]]):
        variant_ids = [variant_id for variant_id, _ in keys]
        attribute_slugs = [attribute_slug for _, attribute_slug in keys]

        def with_attributes_and_products(
            data: tuple[list[product_models.Product], list[Attribute]],
        ):
            products, attributes = data
            product_type_ids = {
                product.product_type_id for product in products if product is not None
            }
            variant_id_to_product_map = {
                variant_id: product
                for (variant_id, _), product in zip(keys, products, strict=False)
            }
            attribute_map = {attr.slug: attr for attr in attributes if attr is not None}

            attribute_variants = (
                AttributeVariant.objects.using(self.database_connection_name)
                .filter(
                    attribute__in=[attr.id for attr in attribute_map.values()],
                    product_type__in=product_type_ids,
                )
                .values_list("attribute_id", "product_type_id")
            )
            product_type_id_to_attribute_ids = defaultdict(set)
            for attribute_id, attr_product_type_id in attribute_variants:
                product_type_id_to_attribute_ids[attr_product_type_id].add(attribute_id)

            response: list[Attribute | None] = []
            for variant_id, attribute_slug in keys:
                attribute = attribute_map.get(attribute_slug)
                if not attribute:
                    response.append(None)
                    continue

                product = variant_id_to_product_map.get(variant_id)
                if not product:
                    response.append(None)
                    continue
                product_type_id = product.product_type_id
                attributes_assigned_to_product_type = (
                    product_type_id_to_attribute_ids.get(product_type_id, set())
                )
                if attribute.id in attributes_assigned_to_product_type:
                    response.append(attribute)
                else:
                    response.append(None)
            return response

        products_loader = ProductByVariantIdLoader(self.context).load_many(variant_ids)
        attributes_loader = AttributesBySlugLoader(self.context).load_many(
            attribute_slugs
        )
        return Promise.all([products_loader, attributes_loader]).then(
            with_attributes_and_products
        )


class AttributesByProductVariantIdAndSelectionAndLimitLoader(
    DataLoader[tuple[VARIANT_ID, LIMIT, VARIANT_SELECTION], list[Attribute]]
):
    context_key = "attribute_ids_by_product_variant_id_and_limit"

    def get_attribute_variant_qs(
        self, product_type_ids: set[int]
    ) -> QuerySet[AttributeVariant]:
        return AttributeVariant.objects.using(self.database_connection_name).filter(
            product_type__in=product_type_ids
        )

    def batch_load(self, keys: Iterable[tuple[VARIANT_ID, LIMIT, VARIANT_SELECTION]]):
        @allow_writer_in_context(self.context)
        def with_products(products: list[product_models.Product]):
            # get attribute variants assigned to product type of the variants
            variant_id_to_product_id_map = {
                variant_id: product.id
                for (variant_id, _, _), product in zip(keys, products, strict=False)
            }
            product_id_to_product_type_id_map = {
                product.id: product.product_type_id for product in products
            }
            product_type_ids = set(product_id_to_product_type_id_map.values())
            attribute_variants = self.get_attribute_variant_qs(
                product_type_ids
            ).values_list("attribute_id", "product_type_id", "variant_selection")

            # create list of attribute ids to fetch for each variant. Use limit and
            # selection to reduce the number of attributes to fetch
            product_type_id_to_attribute_id_and_variant_selection = defaultdict(list)
            for (
                attribute_id,
                attr_product_type_id,
                variant_selection,
            ) in attribute_variants:
                product_type_id_to_attribute_id_and_variant_selection[
                    attr_product_type_id
                ].append((attribute_id, variant_selection))

            attribute_ids = set()
            for variant_id, limit, variant_selection in keys:
                product_id = variant_id_to_product_id_map.get(variant_id)
                if not product_id:
                    continue
                product_type_id = product_id_to_product_type_id_map.get(product_id)
                if not product_type_id:
                    continue
                attribute_ids_and_selections: list[tuple[int, bool]] = (
                    product_type_id_to_attribute_id_and_variant_selection.get(
                        product_type_id, []
                    )
                )

                attribute_ids_to_include = []
                for attr_id, is_variant_selection in attribute_ids_and_selections:
                    if (
                        variant_selection is not None
                        and variant_selection != is_variant_selection
                    ):
                        continue
                    attribute_ids_to_include.append(attr_id)
                attribute_ids.update(attribute_ids_to_include[:limit])

            def get_attributes_for_variants(attributes: list[Attribute]):
                attribute_map = {attr.id: attr for attr in attributes}

                response = []
                # loop over keys to build the response based on the variant_id, limit number and
                # selection provided as an input
                for variant_id, limit, variant_selection in keys:
                    single_response_entry: list[Attribute] = []
                    product_id = variant_id_to_product_id_map.get(variant_id)
                    if not product_id:
                        response.append(single_response_entry)
                        continue
                    product_type_id = product_id_to_product_type_id_map.get(product_id)
                    if not product_type_id:
                        response.append(single_response_entry)
                        continue
                    attribute_ids_and_selections: list[tuple[int, bool]] = (
                        product_type_id_to_attribute_id_and_variant_selection.get(
                            product_type_id, []
                        )[:limit]
                    )
                    for (
                        variant_attribute_id,
                        attribute_selection,
                    ) in attribute_ids_and_selections:
                        if (
                            variant_selection is not None
                            and variant_selection != attribute_selection
                        ):
                            continue
                        attribute = attribute_map.get(variant_attribute_id)
                        if not attribute:
                            continue
                        single_response_entry.append(attribute)
                    response.append(single_response_entry)
                return response

            return (
                AttributesByAttributeId(self.context)
                .load_many(attribute_ids)
                .then(get_attributes_for_variants)
            )

        return (
            ProductByVariantIdLoader(self.context)
            .load_many([variant_id for variant_id, _, _ in keys])
            .then(with_products)
        )


class AttributesVisibleToCustomerByProductVariantIdAndSelectionAndLimitLoader(
    AttributesByProductVariantIdAndSelectionAndLimitLoader
):
    context_key = "attribute_ids_visible_to_customer_by_product_variant_id_and_limit"

    def get_attribute_variant_qs(
        self, product_type_ids: set[int]
    ) -> QuerySet[AttributeVariant]:
        return AttributeVariant.objects.using(self.database_connection_name).filter(
            attribute__visible_in_storefront=True, product_type__in=product_type_ids
        )


class AttributesByPageIdAndLimitLoader(
    DataLoader[tuple[PAGE_ID, LIMIT], list[Attribute]]
):
    context_key = "attribute_ids_by_page_id_and_limit"

    def get_attribute_page_qs(self, page_type_ids: set[int]) -> QuerySet[AttributePage]:
        return AttributePage.objects.using(self.database_connection_name).filter(
            page_type__in=page_type_ids
        )

    def batch_load(self, keys: Iterable[tuple[PAGE_ID, LIMIT]]):
        @allow_writer_in_context(self.context)
        def with_pages(pages: list[page_models.Page]):
            page_id_to_page_type_id_map = {
                page.id: page.page_type_id for page in pages if page
            }
            page_type_ids = set(page_id_to_page_type_id_map.values())

            attribute_pages = (
                self.get_attribute_page_qs(page_type_ids)
                .using(self.database_connection_name)
                .values_list("attribute_id", "page_type_id")
            )

            page_type_id_to_attribute_ids = defaultdict(list)

            for attribute_id, attr_page_type_id in attribute_pages:
                page_type_id_to_attribute_ids[attr_page_type_id].append(attribute_id)

            attribute_ids = set()
            for page_id, limit in keys:
                page_type_id = page_id_to_page_type_id_map.get(page_id)
                if not page_type_id:
                    continue
                attribute_ids.update(
                    page_type_id_to_attribute_ids.get(page_type_id, [])[:limit]
                )

            def get_attributes_for_pages(attributes: list[Attribute]):
                attribute_map = {attr.id: attr for attr in attributes}

                response = []
                for page_id, limit in keys:
                    single_response_entry: list[Attribute] = []
                    page_type_id = page_id_to_page_type_id_map.get(page_id)
                    if not page_type_id:
                        response.append(single_response_entry)
                        continue
                    page_attribute_ids = page_type_id_to_attribute_ids.get(
                        page_type_id, []
                    )[:limit]
                    for page_attribute_id in page_attribute_ids:
                        attribute = attribute_map.get(page_attribute_id)
                        if not attribute:
                            continue
                        single_response_entry.append(attribute)
                    response.append(single_response_entry)
                return response

            return (
                AttributesByAttributeId(self.context)
                .load_many(attribute_ids)
                .then(get_attributes_for_pages)
            )

        page_ids = [page_id for page_id, _ in keys]
        return PageByIdLoader(self.context).load_many(page_ids).then(with_pages)


class AttributesVisibleToCustomerByPageIdAndLimitLoader(
    AttributesByPageIdAndLimitLoader
):
    context_key = "attributes_visible_to_customer_by_page_id_and_limit"

    def get_attribute_page_qs(self, page_type_ids: set[int]) -> QuerySet[AttributePage]:
        return AttributePage.objects.using(self.database_connection_name).filter(
            attribute__visible_in_storefront=True,
            page_type__in=page_type_ids,
        )


class AttributeByPageIdAndAttributeSlugLoader(
    DataLoader[tuple[PAGE_ID, ATTRIBUTE_SLUG], Attribute | None]
):
    context_key = "attribute_by_page_id_and_attribute_slug"

    def batch_load(self, keys: Iterable[tuple[PAGE_ID, ATTRIBUTE_SLUG]]):
        page_ids = [page_id for page_id, _ in keys]
        attribute_slugs = [attribute_slug for _, attribute_slug in keys]

        def with_pages_and_attributes(
            data: tuple[list[page_models.Page], list[Attribute]],
        ):
            pages, attributes = data
            page_type_ids = {page.page_type_id for page in pages if page is not None}
            page_map = {page.id: page for page in pages if page is not None}
            attribute_map = {attr.slug: attr for attr in attributes if attr is not None}
            attribute_pages = (
                AttributePage.objects.using(self.database_connection_name)
                .filter(
                    attribute__in=[attr.id for attr in attribute_map.values()],
                    page_type__in=page_type_ids,
                )
                .values_list("attribute_id", "page_type_id")
            )

            page_type_id_to_attribute_ids = defaultdict(set)
            for attribute_id, page_type_id in attribute_pages:
                page_type_id_to_attribute_ids[page_type_id].add(attribute_id)

            response: list[Attribute | None] = []
            for page_id, attribute_slug in keys:
                attribute = attribute_map.get(attribute_slug)
                if not attribute:
                    response.append(None)
                    continue

                page = page_map.get(page_id)
                if not page:
                    response.append(None)
                    continue
                page_type_id = page.page_type_id
                attributes_assigned_to_page_type = page_type_id_to_attribute_ids.get(
                    page_type_id, set()
                )
                if attribute.id in attributes_assigned_to_page_type:
                    response.append(attribute)
                else:
                    response.append(None)
            return response

        pages_loader = PageByIdLoader(self.context).load_many(page_ids)
        attributes_loader = AttributesBySlugLoader(self.context).load_many(
            attribute_slugs
        )
        return Promise.all([pages_loader, attributes_loader]).then(
            with_pages_and_attributes
        )


class AttributeValuesByProductIdAndAttributeIdAndLimitLoader(
    DataLoader[tuple[PRODUCT_ID, ATTRIBUTE_ID, LIMIT], list[AttributeValue]]
):
    context_key = "attribute_values_by_product_and_attribute"

    def batch_load(self, keys: Iterable[tuple[PRODUCT_ID, ATTRIBUTE_ID, LIMIT]]):
        limit_map = defaultdict(list)
        for product_id, attribute_id, limit in keys:
            limit_map[limit].append((product_id, attribute_id))

        attribute_value_id_to_fetch_map: dict[
            tuple[PRODUCT_ID, ATTRIBUTE_ID, LIMIT], list[int]
        ] = defaultdict(list)

        for limit, values in limit_map.items():
            product_ids = [val[0] for val in values]
            attribute_ids = [val[1] for val in values]

            assigned_attribute_values = AssignedProductAttributeValue.objects.using(
                self.database_connection_name
            ).annotate(attribute_id=F("value__attribute_id"))
            if limit is not None:
                assigned_attribute_values = assigned_attribute_values.annotate(
                    row_num=Window(
                        expression=RowNumber(),
                        partition_by=[F("attribute_id"), F("product_id")],
                        order_by=["sort_order", "pk"],
                    )
                ).filter(row_num__lte=limit)

            assigned_attribute_values = assigned_attribute_values.filter(
                attribute_id__in=attribute_ids,
                product_id__in=product_ids,
            ).values_list("product_id", "value_id", "attribute_id")

            for product_id, value_id, attribute_id in assigned_attribute_values:
                attribute_value_id_to_fetch_map[
                    (product_id, attribute_id, limit)
                ].append(value_id)

        attribute_value_ids_to_fetch = set()
        for id_list in attribute_value_id_to_fetch_map.values():
            attribute_value_ids_to_fetch.update(id_list)

        def with_attribute_values(attribute_values: list[AttributeValue]):
            attribute_value_map = {av.id: av for av in attribute_values}
            response_data: defaultdict[
                tuple[PRODUCT_ID, ATTRIBUTE_ID, LIMIT], list[AttributeValue]
            ] = defaultdict(list)
            for (
                product_id,
                attribute_id,
                limit,
            ), value_ids in attribute_value_id_to_fetch_map.items():
                for value_id in value_ids:
                    attr_val = attribute_value_map.get(value_id)
                    if not attr_val:
                        continue
                    response_data[(product_id, attribute_id, limit)].append(attr_val)
            return [response_data.get(key, []) for key in keys]

        return (
            AttributeValueByIdLoader(self.context)
            .load_many(attribute_value_ids_to_fetch)
            .then(with_attribute_values)
        )


class AttributeValuesByPageIdAndAttributeIdAndLimitLoader(
    DataLoader[tuple[PAGE_ID, ATTRIBUTE_ID, LIMIT], list[AttributeValue]]
):
    context_key = "attribute_values_by_page_and_attribute"

    def batch_load(self, keys: Iterable[tuple[PAGE_ID, ATTRIBUTE_ID, LIMIT]]):
        limit_map = defaultdict(list)
        for page_id, attribute_id, limit in keys:
            limit_map[limit].append((page_id, attribute_id))

        attribute_value_id_to_fetch_map: dict[
            tuple[PAGE_ID, ATTRIBUTE_ID, LIMIT], list[int]
        ] = defaultdict(list)

        for limit, values in limit_map.items():
            page_ids = [val[0] for val in values]
            attribute_ids = [val[1] for val in values]

            assigned_attribute_values = AssignedPageAttributeValue.objects.using(
                self.database_connection_name
            ).annotate(attribute_id=F("value__attribute_id"))
            if limit is not None:
                assigned_attribute_values = assigned_attribute_values.annotate(
                    row_num=Window(
                        expression=RowNumber(),
                        partition_by=[F("attribute_id"), F("page_id")],
                        order_by=["sort_order", "pk"],
                    )
                ).filter(row_num__lte=limit)
            assigned_attribute_values = assigned_attribute_values.filter(
                attribute_id__in=attribute_ids,
                page_id__in=page_ids,
            ).values_list("page_id", "value_id", "attribute_id")

            for page_id, value_id, attribute_id in assigned_attribute_values:
                attribute_value_id_to_fetch_map[(page_id, attribute_id, limit)].append(
                    value_id
                )

        attribute_value_ids_to_fetch = set()
        for id_list in attribute_value_id_to_fetch_map.values():
            attribute_value_ids_to_fetch.update(id_list)

        def with_attribute_values(attribute_values: list[AttributeValue]):
            attribute_value_map = {av.id: av for av in attribute_values}
            response_data: defaultdict[
                tuple[PAGE_ID, ATTRIBUTE_ID, LIMIT], list[AttributeValue]
            ] = defaultdict(list)
            for (
                page_id,
                attribute_id,
                limit,
            ), value_ids in attribute_value_id_to_fetch_map.items():
                for value_id in value_ids:
                    attr_val = attribute_value_map.get(value_id)
                    if not attr_val:
                        continue
                    response_data[(page_id, attribute_id, limit)].append(attr_val)
            return [response_data.get(key, []) for key in keys]

        return (
            AttributeValueByIdLoader(self.context)
            .load_many(attribute_value_ids_to_fetch)
            .then(with_attribute_values)
        )


class AttributeValuesByVariantIdAndAttributeIdAndLimitLoader(
    DataLoader[tuple[VARIANT_ID, ATTRIBUTE_ID, LIMIT], list[AttributeValue]]
):
    context_key = "attribute_values_by_variant_and_attribute"

    def batch_load(self, keys: Iterable[tuple[VARIANT_ID, ATTRIBUTE_ID, LIMIT]]):
        limit_map = defaultdict(list)

        for variant_id, attribute_id, limit in keys:
            limit_map[limit].append((variant_id, attribute_id))

        attribute_value_id_to_fetch_map: dict[
            tuple[VARIANT_ID, ATTRIBUTE_ID, LIMIT], list[int]
        ] = defaultdict(list)

        for limit, values in limit_map.items():
            variant_ids = [val[0] for val in values]
            attribute_ids = [val[1] for val in values]

            assigned_variant_attributes = (
                AssignedVariantAttribute.objects.using(self.database_connection_name)
                .annotate(attribute_id=F("assignment__attribute_id"))
                .filter(
                    variant_id__in=variant_ids,
                    attribute_id__in=attribute_ids,
                )
                .values_list("variant_id", "id", "attribute_id")
            )
            assigned_variant_attributes_map = {
                id_: (variant_id, attribute_id)
                for variant_id, id_, attribute_id in assigned_variant_attributes
            }

            assigned_variant_values = AssignedVariantAttributeValue.objects.using(
                self.database_connection_name
            ).filter(assignment_id__in=assigned_variant_attributes_map.keys())
            if limit is not None:
                assigned_variant_values = assigned_variant_values.annotate(
                    row_num=Window(
                        expression=RowNumber(),
                        partition_by=F("assignment_id"),
                        order_by=["sort_order", "pk"],
                    )
                ).filter(row_num__lte=limit)
            assigned_variant_values = assigned_variant_values.values_list(
                "value_id", "assignment_id"
            )

            for value_id, assignment_id in assigned_variant_values:
                if assignment_id not in assigned_variant_attributes_map:
                    continue
                variant_id, attribute_id = assigned_variant_attributes_map[
                    assignment_id
                ]
                attribute_value_id_to_fetch_map[
                    (variant_id, attribute_id, limit)
                ].append(value_id)

        attribute_value_ids_to_fetch = set()
        for id_list in attribute_value_id_to_fetch_map.values():
            attribute_value_ids_to_fetch.update(id_list)

        def with_attribute_values(attribute_values: list[AttributeValue]):
            attribute_value_map = {av.id: av for av in attribute_values}
            response_data: defaultdict[
                tuple[VARIANT_ID, ATTRIBUTE_ID, LIMIT], list[AttributeValue]
            ] = defaultdict(list)
            for (
                variant_id,
                attribute_id,
                limit,
            ), value_ids in attribute_value_id_to_fetch_map.items():
                for value_id in value_ids:
                    attr_val = attribute_value_map.get(value_id)
                    if not attr_val:
                        continue
                    response_data[(variant_id, attribute_id, limit)].append(attr_val)
            return [response_data.get(key, []) for key in keys]

        return (
            AttributeValueByIdLoader(self.context)
            .load_many(attribute_value_ids_to_fetch)
            .then(with_attribute_values)
        )
