from collections import defaultdict, namedtuple
from typing import TYPE_CHECKING, Dict, List, Optional, Set, Union
from urllib.parse import urljoin

import graphene
from django.conf import settings
from django.db.models import Case, CharField
from django.db.models import Value as V
from django.db.models import When
from django.db.models.functions import Cast, Concat

from ...attribute import AttributeInputType
from ...core.utils import build_absolute_uri
from ...core.utils.editorjs import clean_editor_js
from . import ProductExportFields

if TYPE_CHECKING:
    from django.db.models import QuerySet


def get_products_data(
    queryset: "QuerySet",
    export_fields: Set[str],
    attribute_ids: Optional[List[int]],
    warehouse_ids: Optional[List[int]],
    channel_ids: Optional[List[int]],
) -> List[Dict[str, Union[str, bool]]]:
    """Create data list of products and their variants with fields values.

    It return list with product and variant data which can be used as import to
    csv writer and list of attribute and warehouse headers.
    """

    products_with_variants_data = []
    export_variant_id = "variants__id" in export_fields

    product_fields = set(
        ProductExportFields.HEADERS_TO_FIELDS_MAPPING["fields"].values()
    )
    product_export_fields = export_fields & product_fields
    if not export_variant_id:
        product_export_fields.add("variants__id")

    products_data = (
        queryset.annotate(
            product_weight=Case(
                When(weight__isnull=False, then=Concat("weight", V(" g"))),
                default=V(""),
                output_field=CharField(),
            ),
            variant_weight=Case(
                When(
                    variants__weight__isnull=False,
                    then=Concat("variants__weight", V(" g")),
                ),
                default=V(""),
                output_field=CharField(),
            ),
            description_as_str=Cast("description", CharField()),
        )
        .order_by("pk", "variants__pk")
        .values(*product_export_fields)
        .distinct("pk", "variants__pk")
    )

    products_relations_data = get_products_relations_data(
        queryset, export_fields, attribute_ids, channel_ids
    )

    variants_relations_data = get_variants_relations_data(
        queryset, export_fields, attribute_ids, warehouse_ids, channel_ids
    )

    for product_data in products_data:
        pk = product_data["id"]
        if export_variant_id:
            variant_pk = product_data.get("variants__id")
        else:
            variant_pk = product_data.pop("variants__id")

        product_relations_data: Dict[str, str] = products_relations_data.get(pk, {})
        variant_relations_data: Dict[str, str] = variants_relations_data.get(
            variant_pk, {}
        )

        product_data["id"] = graphene.Node.to_global_id("Product", pk)
        if export_variant_id:
            product_data["variants__id"] = graphene.Node.to_global_id(
                "ProductVariant", variant_pk
            )

        data = {**product_data, **product_relations_data, **variant_relations_data}

        products_with_variants_data.append(data)

    return products_with_variants_data


def get_products_relations_data(
    queryset: "QuerySet",
    export_fields: Set[str],
    attribute_ids: Optional[List[int]],
    channel_ids: Optional[List[int]],
) -> Dict[int, Dict[str, str]]:
    """Get data about product relations fields.

    If any many to many fields are in export_fields or some attribute_ids exists then
    dict with product relations fields is returned.
    Otherwise it returns empty dict.
    """
    many_to_many_fields = set(
        ProductExportFields.HEADERS_TO_FIELDS_MAPPING["product_many_to_many"].values()
    )
    relations_fields = export_fields & many_to_many_fields
    if relations_fields or attribute_ids or channel_ids:
        return prepare_products_relations_data(
            queryset, relations_fields, attribute_ids, channel_ids
        )

    return {}


def prepare_products_relations_data(
    queryset: "QuerySet",
    fields: Set[str],
    attribute_ids: Optional[List[int]],
    channel_ids: Optional[List[int]],
) -> Dict[int, Dict[str, str]]:
    """Prepare data about products relation fields for given queryset.

    It return dict where key is a product pk, value is a dict with relation fields data.
    """
    attribute_fields = ProductExportFields.PRODUCT_ATTRIBUTE_FIELDS
    channel_fields = ProductExportFields.PRODUCT_CHANNEL_LISTING_FIELDS.copy()
    result_data: Dict[int, dict] = defaultdict(dict)

    fields.add("pk")
    if attribute_ids:
        fields.update(attribute_fields.values())
    if channel_ids:
        fields.update(channel_fields.values())

    relations_data = queryset.values(*fields)

    channel_pk_lookup = channel_fields.pop("channel_pk")
    channel_slug_lookup = channel_fields.pop("slug")
    for data in relations_data.iterator():
        pk = data.get("pk")
        collection = data.get("collections__slug")
        image = data.pop("media__image", None)

        result_data = add_image_uris_to_data(pk, image, "media__image", result_data)
        result_data = add_collection_info_to_data(pk, collection, result_data)

        result_data, data = handle_attribute_data(
            pk, data, attribute_ids, result_data, attribute_fields, "product attribute"
        )
        result_data, data = handle_channel_data(
            pk,
            data,
            channel_ids,
            result_data,
            channel_pk_lookup,
            channel_slug_lookup,
            channel_fields,
        )

    result: Dict[int, Dict[str, str]] = {
        pk: {
            header: ", ".join(sorted(values)) if isinstance(values, set) else values
            for header, values in data.items()
        }
        for pk, data in result_data.items()
    }
    return result


def get_variants_relations_data(
    queryset: "QuerySet",
    export_fields: Set[str],
    attribute_ids: Optional[List[int]],
    warehouse_ids: Optional[List[int]],
    channel_ids: Optional[List[int]],
) -> Dict[int, Dict[str, str]]:
    """Get data about variants relations fields.

    If any many to many fields are in export_fields or some attribute_ids or
    warehouse_ids exists then dict with variant relations fields is returned.
    Otherwise it returns empty dict.
    """
    many_to_many_fields = set(
        ProductExportFields.HEADERS_TO_FIELDS_MAPPING["variant_many_to_many"].values()
    )
    relations_fields = export_fields & many_to_many_fields
    if relations_fields or attribute_ids or warehouse_ids or channel_ids:
        return prepare_variants_relations_data(
            queryset, relations_fields, attribute_ids, warehouse_ids, channel_ids
        )

    return {}


def prepare_variants_relations_data(
    queryset: "QuerySet",
    fields: Set[str],
    attribute_ids: Optional[List[int]],
    warehouse_ids: Optional[List[int]],
    channel_ids: Optional[List[int]],
) -> Dict[int, Dict[str, str]]:
    """Prepare data about variants relation fields for given queryset.

    It return dict where key is a product pk, value is a dict with relation fields data.
    """
    attribute_fields = ProductExportFields.VARIANT_ATTRIBUTE_FIELDS
    warehouse_fields = ProductExportFields.WAREHOUSE_FIELDS
    channel_fields = ProductExportFields.VARIANT_CHANNEL_LISTING_FIELDS.copy()

    result_data: Dict[int, dict] = defaultdict(dict)
    fields.add("variants__pk")

    if attribute_ids:
        fields.update(attribute_fields.values())
    if warehouse_ids:
        fields.update(warehouse_fields.values())
    if channel_ids:
        fields.update(channel_fields.values())

    relations_data = queryset.values(*fields)

    channel_pk_lookup = channel_fields.pop("channel_pk")
    channel_slug_lookup = channel_fields.pop("slug")

    for data in relations_data.iterator():
        pk = data.get("variants__pk")
        image = data.pop("variants__media__image", None)

        result_data = add_image_uris_to_data(
            pk, image, "variants__media__image", result_data
        )
        result_data, data = handle_attribute_data(
            pk, data, attribute_ids, result_data, attribute_fields, "variant attribute"
        )
        result_data, data = handle_channel_data(
            pk,
            data,
            channel_ids,
            result_data,
            channel_pk_lookup,
            channel_slug_lookup,
            channel_fields,
        )
        result_data, data = handle_warehouse_data(
            pk, data, warehouse_ids, result_data, warehouse_fields
        )

    result: Dict[int, Dict[str, str]] = {
        pk: {
            header: ", ".join(sorted(values)) if isinstance(values, set) else values
            for header, values in data.items()
        }
        for pk, data in result_data.items()
    }
    return result


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


def add_image_uris_to_data(
    pk: int, image: str, header: str, result_data: Dict[int, dict]
) -> Dict[int, dict]:
    """Add absolute uri of given image path to product or variant data.

    This function based on given image path creates absolute uri and adds it to dict
    with variant or product data. If some info about images already exists in data,
    absolute uri of given image is added to set with other uris.
    """
    if image:
        uri = build_absolute_uri(urljoin(settings.MEDIA_URL, image))
        if header in result_data[pk]:
            result_data[pk][header].add(uri)
        else:
            result_data[pk][header] = {uri}
    return result_data


AttributeData = namedtuple(
    "AttributeData",
    [
        "slug",
        "input_type",
        "entity_type",
        "unit",
        "value_slug",
        "value_name",
        "value",
        "file_url",
        "rich_text",
        "boolean",
        "date_time",
        "reference_page",
        "reference_product",
    ],
)


def handle_attribute_data(
    pk: int,
    data: dict,
    attribute_ids: Optional[List[int]],
    result_data: Dict[int, dict],
    attribute_fields: dict,
    attribute_owner: str,
):
    attribute_pk = str(data.pop(attribute_fields["attribute_pk"], ""))
    attribute_data = AttributeData(
        slug=data.pop(attribute_fields["slug"], None),
        input_type=data.pop(attribute_fields["input_type"], None),
        file_url=data.pop(attribute_fields["file_url"], None),
        value_slug=data.pop(attribute_fields["value_slug"], None),
        value_name=data.pop(attribute_fields["value_name"], None),
        value=data.pop(attribute_fields["value"], None),
        entity_type=data.pop(attribute_fields["entity_type"], None),
        unit=data.pop(attribute_fields["unit"], None),
        rich_text=data.pop(attribute_fields["rich_text"], None),
        boolean=data.pop(attribute_fields["boolean"], None),
        date_time=data.pop(attribute_fields["date_time"], None),
        reference_page=data.pop(attribute_fields["value_reference_page"], None),
        reference_product=data.pop(attribute_fields["value_reference_product"], None),
    )

    if attribute_ids and attribute_pk in attribute_ids:
        result_data = add_attribute_info_to_data(
            pk, attribute_data, attribute_owner, result_data
        )

    return result_data, data


def handle_channel_data(
    pk: int,
    data: dict,
    channel_ids: Optional[List[int]],
    result_data: Dict[int, dict],
    pk_lookup: str,
    slug_lookup: str,
    fields: dict,
):
    channel_data: dict = {}

    channel_pk = str(data.pop(pk_lookup, ""))
    channel_data = {
        "slug": data.pop(slug_lookup, None),
    }
    for field, lookup in fields.items():
        channel_data[field] = data.pop(lookup, None)

    if channel_ids and channel_pk in channel_ids:
        result_data = add_channel_info_to_data(
            pk, channel_data, result_data, list(fields.keys())
        )

    return result_data, data


def handle_warehouse_data(
    pk: int,
    data: dict,
    warehouse_ids: Optional[List[int]],
    result_data: Dict[int, dict],
    warehouse_fields: dict,
):
    warehouse_data: dict = {}

    warehouse_pk = str(data.pop(warehouse_fields["warehouse_pk"], ""))
    warehouse_data = {
        "slug": data.pop(warehouse_fields["slug"], None),
        "qty": data.pop(warehouse_fields["quantity"], None),
    }

    if warehouse_ids and warehouse_pk in warehouse_ids:
        result_data = add_warehouse_info_to_data(pk, warehouse_data, result_data)

    return result_data, data


def add_attribute_info_to_data(
    pk: int,
    attribute_data: AttributeData,
    attribute_owner: str,
    result_data: Dict[int, dict],
) -> Dict[int, dict]:
    """Add info about attribute to variant or product data.

    This functions adds info about attribute to dict with variant or product data.
    If attribute with given slug already exists in data, attribute value is added
    to set with values.
    It returns updated data.
    """
    slug = attribute_data.slug
    header = None

    if not slug:
        return result_data

    header = f"{slug} ({attribute_owner})"
    value = prepare_attribute_value(attribute_data)

    if header in result_data[pk]:
        result_data[pk][header].add(value)  # type: ignore
    else:
        result_data[pk][header] = {value}

    return result_data


def prepare_attribute_value(attribute_data: AttributeData):
    """Prepare value of attribute value depending on the attribute input type."""
    input_type = attribute_data.input_type
    if input_type == AttributeInputType.FILE:
        file_url = attribute_data.file_url
        value = (
            build_absolute_uri(urljoin(settings.MEDIA_URL, file_url))
            if file_url
            else ""
        )
    elif input_type == AttributeInputType.REFERENCE and (
        attribute_data.reference_page or attribute_data.reference_product
    ):
        if attribute_data.reference_page:
            reference_id = attribute_data.reference_page
        else:
            reference_id = attribute_data.reference_product
        value = f"{attribute_data.entity_type}_{reference_id}"
    elif input_type == AttributeInputType.NUMERIC:
        value = f"{attribute_data.value_name}"
        if attribute_data.unit:
            value += f" {attribute_data.unit}"
    elif input_type == AttributeInputType.RICH_TEXT:
        value = clean_editor_js(attribute_data.rich_text, to_string=True)
    elif (
        input_type == AttributeInputType.BOOLEAN and attribute_data.boolean is not None
    ):
        value = str(attribute_data.boolean)
    elif input_type == AttributeInputType.DATE:
        value = str(attribute_data.date_time.date())
    elif input_type == AttributeInputType.DATE_TIME:
        value = str(attribute_data.date_time)
    elif input_type == AttributeInputType.SWATCH:
        if attribute_data.file_url:
            value = build_absolute_uri(
                urljoin(settings.MEDIA_URL, attribute_data.file_url)
            )
        else:
            value = attribute_data.value
    else:
        value = attribute_data.value_name or attribute_data.value_slug or ""

    return value


def add_warehouse_info_to_data(
    pk: int,
    warehouse_data: Dict[str, Union[Optional[str]]],
    result_data: Dict[int, dict],
) -> Dict[int, dict]:
    """Add info about stock quantity to variant data.

    This functions adds info about stock quantity to dict with variant data.
    It returns updated data.
    """

    slug = warehouse_data["slug"]
    if slug:
        warehouse_qty_header = f"{slug} (warehouse quantity)"
        if warehouse_qty_header not in result_data[pk]:
            result_data[pk][warehouse_qty_header] = warehouse_data["qty"]

    return result_data


def add_channel_info_to_data(
    pk: int,
    channel_data: Dict[str, Union[Optional[str]]],
    result_data: Dict[int, dict],
    fields: List[str],
) -> Dict[int, dict]:
    """Add info about channel currency code, whether is published and publication date.

    This functions adds info about channel to dict with product data.
    It returns updated data.
    """
    slug = channel_data["slug"]
    if slug:
        for field in fields:
            header = f"{slug} (channel {field.replace('_', ' ')})"
            if header not in result_data[pk]:
                result_data[pk][header] = channel_data[field]

    return result_data
