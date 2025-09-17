from collections import defaultdict
from collections.abc import Iterable

from ....attribute.models import Attribute
from ....page.models import PageType
from ....product.models import ProductType
from ...core.dataloaders import DataLoader
from ...page.dataloaders import PageTypeByIdLoader
from ...product.dataloaders import ProductTypeByIdLoader

type LIMIT = int | None
type PAGE_TYPE_ID = int
type ATTRIBUTE_ID = int


class AttributeReferenceProductTypesByAttributeIdAndLimitLoader(
    DataLoader[tuple[ATTRIBUTE_ID, LIMIT], list[ProductType]]
):
    context_key = "attributereferenceproducttypes_by_attributeid_and_limit"

    def batch_load(self, keys: Iterable[tuple[ATTRIBUTE_ID, LIMIT]]):
        ReferenceTypeModel = Attribute.reference_product_types.through
        attribute_ids = [attribute_id for attribute_id, _ in keys]
        reference_types = (
            ReferenceTypeModel.objects.using(self.database_connection_name).filter(
                attribute_id__in=attribute_ids
            )
        ).values_list("attribute_id", "producttype_id")

        attribute_id_to_product_type_ids = defaultdict(list)
        for attribute_id, producttype_id in reference_types:
            attribute_id_to_product_type_ids[attribute_id].append(producttype_id)

        product_type_ids = set()
        for attribute_id, limit in keys:
            product_type_ids.update(
                attribute_id_to_product_type_ids.get(attribute_id, [])[:limit]
            )

        def get_reference_types(product_types):
            response = []
            product_type_map = {
                product_type.id: product_type for product_type in product_types
            }
            for attribute_id, limit in keys:
                product_type_ids = attribute_id_to_product_type_ids.get(
                    attribute_id, []
                )[:limit]
                single_response_entry: list[ProductType] = []
                for product_type_id in product_type_ids:
                    if product_type := product_type_map.get(product_type_id):
                        single_response_entry.append(product_type)
                response.append(single_response_entry)
            return response

        return (
            ProductTypeByIdLoader(self.context)
            .load_many(list(product_type_ids))
            .then(get_reference_types)
        )


class AttributeReferencePageTypesByAttributeIdAndLimitLoader(
    DataLoader[tuple[ATTRIBUTE_ID, LIMIT], list[PageType]]
):
    context_key = "attributereferencepagetypes_by_attributeid_and_limit"

    def batch_load(self, keys: Iterable[tuple[ATTRIBUTE_ID, LIMIT]]):
        ReferenceTypeModel = Attribute.reference_page_types.through
        attribute_ids = [attribute_id for attribute_id, _ in keys]
        reference_types = (
            ReferenceTypeModel.objects.using(self.database_connection_name).filter(
                attribute_id__in=attribute_ids
            )
        ).values_list("attribute_id", "pagetype_id")

        attribute_id_to_page_type_ids = defaultdict(list)
        for attribute_id, pagetype_id in reference_types:
            attribute_id_to_page_type_ids[attribute_id].append(pagetype_id)

        page_type_ids = set()
        for attribute_id, limit in keys:
            page_type_ids.update(
                attribute_id_to_page_type_ids.get(attribute_id, [])[:limit]
            )

        def get_reference_types(page_types):
            response = []
            page_type_map = {page_type.id: page_type for page_type in page_types}
            for attribute_id, limit in keys:
                page_type_ids = attribute_id_to_page_type_ids.get(attribute_id, [])[
                    :limit
                ]
                single_response_entry: list[PageType] = []
                for page_type_id in page_type_ids:
                    if page_type := page_type_map.get(page_type_id):
                        single_response_entry.append(page_type)
                response.append(single_response_entry)
            return response

        return (
            PageTypeByIdLoader(self.context)
            .load_many(list(page_type_ids))
            .then(get_reference_types)
        )
