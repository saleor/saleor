import os
from collections import ChainMap, defaultdict
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Tuple, Union

from django.conf import settings
from django.db.models import Case, CharField, F, Value as V, When
from django.db.models.functions import Concat

from ...core.utils import build_absolute_uri
from ...product.models import Attribute, ProductVariant
from ...warehouse.models import Warehouse

if TYPE_CHECKING:
    # flake8: noqa
    from django.db.models import QuerySet


class ProductExportFields:
    """Data structure with fields for product export."""

    HEADERS_TO_FIELDS_MAPPING = {
        "product_fields": {
            "id": "id",
            "name": "name",
            "description": "description",
            "visible": "is_published",
            "category": "category__slug",
            "product type": "product_type__name",
            "charge taxes": "charge_taxes",
            "product weight": "product_weight",
            "price": "price_amount",
            "product currency": "product_currency",
        },
        "product_many_to_many": {
            "collections": "collections__slug",
            "product images": "product_image_path",
        },
        "variant_fields": {
            "variant sku": "sku",
            "variant weight": "variant_weight",
            "variant images": "variant_image_path",
            "cost price": "cost_price_amount",
            "price override": "price_override_amount",
            "variant currency": "variant_currency",
        },
    }

    WAREHOUSE_FIELDS = {
        "slug": "stocks__warehouse__slug",
        "quantity": "stocks__quantity",
        "warehouse_pk": "stocks__warehouse__id",
    }

    ATTRIBUTE_FIELDS = {
        "value": "attributes__values__slug",
        "slug": "attributes__assignment__attribute__slug",
        "attribute_pk": "attributes__assignment__attribute__pk",
    }


def get_export_fields_and_headers_info(export_info: Dict[str, list]):
    """Get export fields, all headers and headers mapping.

    Based on export_info returns exported fields, fields to headers mapping and
    all headers.
    Headers contains product, variant, attribute and warehouse headers.
    """
    export_fields, csv_headers_mapping = get_product_export_fields_and_headers(
        export_info
    )
    attributes_headers = get_attributes_headers(export_info)
    warehouses_headers = get_warehouses_headers(export_info)

    headers = export_fields + attributes_headers + warehouses_headers
    return export_fields, csv_headers_mapping, headers


def get_product_export_fields_and_headers(export_info: Dict[str, list]):
    """Get export fields from export info and prepare headers mapping.

    Based on given fields headers from export info, export fields set and
    headers mapping is prepared.
    """
    export_fields = ["id"]
    csv_headers_mapping: Dict[str, str] = {}

    fields = export_info.get("fields")
    if not fields:
        return export_fields, csv_headers_mapping

    fields_mapping = dict(
        ChainMap(*reversed(ProductExportFields.HEADERS_TO_FIELDS_MAPPING.values()))  # type: ignore
    )

    for field in fields:
        lookup_field = fields_mapping[field]
        export_fields.append(lookup_field)
        csv_headers_mapping[lookup_field] = field
        # if price is exported, currency is needed too
        if field == "price":
            lookup_field = fields_mapping["product currency"]
            export_fields.append(lookup_field)
            csv_headers_mapping[lookup_field] = "product currency"
        elif field == "price override":
            lookup_field = fields_mapping["variant currency"]
            export_fields.append(lookup_field)
            csv_headers_mapping[lookup_field] = "variant currency"

    return export_fields, csv_headers_mapping


def get_attributes_headers(export_info: Dict[str, list]):
    """Get headers for exported attributes.

    Headers are build from slug and contains information if it's a product or variant
    attribute. Respectively for product: "slug-value (product attribute)"
    and for variant: "slug-value (variant attribute)".
    """

    attribute_ids = export_info.get("attributes")
    if not attribute_ids:
        return []

    attributes = Attribute.objects.filter(pk__in=attribute_ids)

    products_headers = (
        attributes.filter(product_types__isnull=False)
        .annotate(header=Concat("slug", V(" (product attribute)")))
        .values_list("header", flat=True)
    )

    variant_headers = (
        attributes.filter(product_variant_types__isnull=False)
        .annotate(header=Concat("slug", V(" (variant attribute)")))
        .values_list("header", flat=True)
    )

    return list(products_headers) + list(variant_headers)


def get_warehouses_headers(export_info: Dict[str, list]):
    warehouse_ids = export_info.get("warehouses")
    if not warehouse_ids:
        return []

    warehouses_headers = (
        Warehouse.objects.filter(pk__in=warehouse_ids)
        .annotate(header=Concat("slug", V(" (warehouse quantity)")))
        .values_list("header", flat=True)
    )

    return list(warehouses_headers)


def get_products_data(
    queryset: "QuerySet",
    export_fields: Set[str],
    warehouse_ids: Optional[List[int]],
    attribute_ids: Optional[List[int]],
) -> List[Dict[str, Union[str, bool]]]:
    """Create data list of products and their variants with fields values.

    It return list with product and variant data which can be used as import to
    csv writer and list of attribute and warehouse headers.
    """

    products_with_variants_data = []

    product_fields = set(
        ProductExportFields.HEADERS_TO_FIELDS_MAPPING["product_fields"].values()
    )
    product_export_fields = export_fields & product_fields

    products_data = queryset.annotate(
        product_currency=F("currency"),
        product_weight=Case(
            When(weight__isnull=False, then=Concat("weight", V(" g"))),
            default=V(""),
            output_field=CharField(),
        ),
    ).values(*product_export_fields)

    product_relations_data = get_products_relations_data(
        queryset, export_fields, attribute_ids
    )

    variant_fields = set(
        ProductExportFields.HEADERS_TO_FIELDS_MAPPING["variant_fields"].values()
    )
    variant_export_fields = export_fields & variant_fields
    export_variant_data = variant_export_fields or attribute_ids or warehouse_ids
    for product_data in products_data.iterator():
        pk = product_data["id"]
        relations_data: Dict[str, str] = product_relations_data.get(pk, {})
        data = {**product_data, **relations_data}

        if not export_variant_data:
            products_with_variants_data.append(data)
            continue

        variants_data = prepare_variants_data(
            pk, data, variant_export_fields, warehouse_ids, attribute_ids
        )
        products_with_variants_data.extend(variants_data)

    return products_with_variants_data


def get_products_relations_data(
    queryset: "QuerySet", export_fields: Set[str], attribute_ids: Optional[List[int]]
):
    """Get data about product relations fields.

    If any many to many fields are in export_fields or some attribute_ids exists then
    dict with product relations fields is returned. It also returns set with
    attribute headers.
    Otherwise it returns empty dict and set.
    """
    many_to_many_fields = set(
        ProductExportFields.HEADERS_TO_FIELDS_MAPPING["product_many_to_many"].values()
    )
    relations_fields = export_fields & many_to_many_fields
    if relations_fields or attribute_ids:
        return prepare_products_relations_data(
            queryset, relations_fields, attribute_ids
        )

    return {}


def prepare_products_relations_data(
    queryset: "QuerySet", fields: Set[str], attribute_ids: Optional[List[int]]
) -> Dict[int, Dict[str, str]]:
    """Prepare data about products relation fields for given queryset.

    It return dict where key is a product pk, value is a dict with relation fields data.
    It also returns set with attribute headers.
    """
    result_data: Dict[int, dict] = defaultdict(dict)
    if attribute_ids:
        result_data = prepare_attribute_products_data(queryset, attribute_ids)

    if fields:
        fields.add("pk")

        relations_data = queryset.annotate(
            product_image_path=F("images__image"),
        ).values(*fields)

        for data in relations_data.iterator():
            pk = data.get("pk")
            collection = data.get("collections__slug")
            image = data.pop("product_image_path", None)

            result_data = add_image_uris_to_data(
                pk, image, "product_image_path", result_data
            )
            result_data = add_collection_info_to_data(pk, collection, result_data)

    result: Dict[int, Dict[str, str]] = {
        pk: {header: ", ".join(sorted(values)) for header, values in data.items()}
        for pk, data in result_data.items()
    }
    return result


def prepare_attribute_products_data(
    queryset: "QuerySet", attribute_ids: Optional[List[int]],
):
    result_data: Dict[int, dict] = defaultdict(dict)

    attribute_fields = ProductExportFields.ATTRIBUTE_FIELDS
    fields = set(attribute_fields.values())
    fields.add("pk")

    attribute_data = queryset.filter(
        attributes__assignment__attribute__pk__in=attribute_ids
    ).values(*fields)

    for data in attribute_data.iterator():
        pk = data.get("pk")
        attribute = {
            "slug": data[attribute_fields["slug"]],
            "value": data[attribute_fields["value"]],
        }
        result_data = add_attribute_info_to_data(
            pk, attribute, "product attribute", result_data
        )

    return result_data


def add_collection_info_to_data(
    pk: int, collection: str, result_data: Dict[int, dict]
) -> Dict[int, dict]:
    """Add collection info to product data.

    This functions adds info about collection to dict with product data.
    If some collection info already exists in data, collection slug is added
    to set with other values.
    It returns updated product data.
    """

    if collection:
        header = "collections__slug"
        if header in result_data[pk]:
            result_data[pk][header].add(collection)  # type: ignore
        else:
            result_data[pk][header] = {collection}
    return result_data


def prepare_variants_data(
    pk: int,
    product_data: dict,
    variant_fields: Set[str],
    warehouse_ids: Optional[List[int]],
    attribute_ids: Optional[List[int]],
) -> List[dict]:
    """Prepare variants data for product with given pk.

    This function gets product pk and prepared data about product"s variants.
    Returned data contains info about variant fields and relations.
    It also return sets with variant attributes and warehouse headers.
    """
    variant_fields.add("pk")

    if attribute_ids:
        variant_fields.update(ProductExportFields.ATTRIBUTE_FIELDS.values())
    if warehouse_ids:
        variant_fields.update(ProductExportFields.WAREHOUSE_FIELDS.values())

    variants_data = (
        ProductVariant.objects.filter(product__pk=pk)
        .annotate(
            variant_currency=F("currency"),
            variant_image_path=F("images__image"),
            variant_weight=Case(
                When(weight__isnull=False, then=Concat("weight", V(" g"))),
                default=V(""),
                output_field=CharField(),
            ),
        )
        .order_by("sku")
        .values(*variant_fields)
    )

    result_data = update_variant_data(
        variants_data, product_data, warehouse_ids, attribute_ids
    )

    result = [
        {
            header: ", ".join(sorted(values)) if isinstance(values, set) else values
            for header, values in data.items()
        }
        for pk, data in result_data.items()
    ]
    return result


def update_variant_data(
    variants_data: "QuerySet",
    product_data: dict,
    warehouse_ids: Optional[List[int]],
    attribute_ids: Optional[List[int]],
) -> Dict[int, dict]:
    """Update variant data with info about relations fields.

    This function gets dict with variants data and updated it with info
    about relations fields.
    It return dict with updated info and sets of attributes and warehouse headers.
    """
    warehouse_fields = ProductExportFields.WAREHOUSE_FIELDS
    attribute_fields = ProductExportFields.ATTRIBUTE_FIELDS

    result_data: Dict[int, dict] = defaultdict(dict)

    for data in variants_data.iterator():
        pk: int = data.pop("pk")  # type: ignore
        attribute_data: dict = {}
        warehouse_data: dict = {}

        attribute_pk = str(data.pop(attribute_fields["attribute_pk"], ""))
        attribute_data = {
            "slug": data.pop(attribute_fields["slug"], None),
            "value": data.pop(attribute_fields["value"], None),
        }

        warehouse_pk = str(data.pop(warehouse_fields["warehouse_pk"], ""))
        warehouse_data = {
            "slug": data.pop(warehouse_fields["slug"], None),
            "qty": data.pop(warehouse_fields["quantity"], None),
        }

        image: str = data.pop("variant_image_path", None)  # type: ignore

        if pk not in result_data:
            # add product data to variant row
            data.update(product_data)
            result_data[pk] = data

        if attribute_ids and attribute_pk in attribute_ids:
            result_data = add_attribute_info_to_data(
                pk, attribute_data, "variant attribute", result_data
            )

        if warehouse_ids and warehouse_pk in warehouse_ids:
            result_data = add_warehouse_info_to_data(pk, warehouse_data, result_data)

        result_data = add_image_uris_to_data(
            pk, image, "variant_image_path", result_data
        )

    return result_data


def add_image_uris_to_data(
    pk: int, image: str, header: str, result_data: Dict[int, dict]
) -> Dict[int, dict]:
    """Add absolute uri of given image path to product or variant data.

    This function based on given image path creates absolute uri and adds it to dict
    with variant or product data. If some info about images already exists in data,
    absolute uri of given image is added to set with other uris.
    """
    if image:
        uri = build_absolute_uri(os.path.join(settings.MEDIA_URL, image))
        if header in result_data[pk]:
            result_data[pk][header].add(uri)
        else:
            result_data[pk][header] = {uri}
    return result_data


def add_attribute_info_to_data(
    pk: int,
    attribute_data: Dict[str, Optional[Union[str]]],
    attribute_owner: str,
    result_data: Dict[int, dict],
) -> Dict[int, dict]:
    """Add info about attribute to variant or product data.

    This functions adds info about attribute to dict with variant or product data.
    If attribute with given slug already exists in data, attribute value is added
    to set with values.
    It returns updated data and attribute header created based on attribute slug.
    """
    slug = attribute_data["slug"]
    header = None
    if slug:
        header = f"{slug} ({attribute_owner})"
        if header in result_data[pk]:
            result_data[pk][header].add(attribute_data["value"])  # type: ignore
        else:
            result_data[pk][header] = {attribute_data["value"]}
    return result_data


def add_warehouse_info_to_data(
    pk: int,
    warehouse_data: Dict[str, Union[Optional[str]]],
    result_data: Dict[int, dict],
) -> Dict[int, dict]:
    """Add info about stock quantity to variant data.

    This functions adds info about stock quantity to dict with variant data.
    It returns updated data and warehouse header created based on warehouse slug.
    """

    slug = warehouse_data["slug"]
    warehouse_header = None
    if slug:
        warehouse_qty_header = f"{slug} (warehouse quantity)"
        if warehouse_qty_header not in result_data[pk]:
            result_data[pk][warehouse_qty_header] = warehouse_data["qty"]
            warehouse_header = warehouse_qty_header

    return result_data
