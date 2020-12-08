from .....attribute.models import Attribute
from .....channel.models import Channel
from .....graphql.csv.enums import ProductFieldEnum
from ....utils.product_headers import (
    get_attributes_headers,
    get_channels_headers,
    get_export_fields_and_headers_info,
    get_product_export_fields_and_headers,
    get_warehouses_headers,
)


def test_get_export_fields_and_headers_fields_without_price():
    # given
    export_info = {
        "fields": [
            ProductFieldEnum.COLLECTIONS.value,
            ProductFieldEnum.DESCRIPTION.value,
            ProductFieldEnum.VARIANT_SKU.value,
        ],
        "warehoses": [],
    }

    # when
    export_fields, file_headers = get_product_export_fields_and_headers(export_info)

    # then
    expected_headers = ["id", "collections", "description", "variant sku"]

    assert set(export_fields) == {
        "collections__slug",
        "id",
        "variants__sku",
        "description",
    }
    assert file_headers == expected_headers


def test_get_export_fields_and_headers_no_fields():
    export_fields, file_headers = get_product_export_fields_and_headers({})

    assert export_fields == ["id"]
    assert file_headers == ["id"]


def test_get_attributes_headers(product_with_multiple_values_attributes):
    # given
    attribute_ids = Attribute.objects.values_list("id", flat=True)
    export_info = {"attributes": attribute_ids}

    # when
    attributes_headers = get_attributes_headers(export_info)

    # then
    product_headers = []
    variant_headers = []
    for attr in Attribute.objects.all():
        if attr.product_types.exists():
            product_headers.append(f"{attr.slug} (product attribute)")
        if attr.product_variant_types.exists():
            variant_headers.append(f"{attr.slug} (variant attribute)")

    expected_headers = product_headers + variant_headers
    assert attributes_headers == expected_headers


def test_get_attributes_headers_lack_of_attributes_ids():
    # given
    export_info = {}

    # when
    attributes_headers = get_attributes_headers(export_info)

    # then
    assert attributes_headers == []


def test_get_warehouses_headers(warehouses):
    # given
    warehouse_ids = [warehouses[0].pk]
    export_info = {"warehouses": warehouse_ids}

    # when
    warehouse_headers = get_warehouses_headers(export_info)

    # then
    assert warehouse_headers == [f"{warehouses[0].slug} (warehouse quantity)"]


def test_get_warehouses_headers_lack_of_warehouse_ids():
    # given
    export_info = {}

    # when
    warehouse_headers = get_warehouses_headers(export_info)

    # then
    assert warehouse_headers == []


def test_get_channels_headers(channel_USD, channel_PLN):
    # given
    channel_usd_slug = channel_USD.slug
    channel_pln_slug = channel_PLN.slug

    channel_ids = [channel_USD.pk, channel_PLN.pk]
    export_info = {"channels": channel_ids}

    # when
    channel_headers = get_channels_headers(export_info)

    # then
    expected_headers = []
    for channel_slug in [channel_pln_slug, channel_usd_slug]:
        for field in [
            "product currency code",
            "published",
            "publication date",
            "searchable",
            "available for purchase",
            "price amount",
            "variant currency code",
            "variant cost price",
        ]:
            expected_headers.append(f"{channel_slug} (channel {field})")
    assert channel_headers == expected_headers


def test_get_channels_headers_lack_of_channel_ids():
    # given
    export_info = {}

    # when
    channel_headers = get_channels_headers(export_info)

    # then
    assert channel_headers == []


def test_get_export_fields_and_headers_info(
    warehouses, product_with_multiple_values_attributes, channel_PLN, channel_USD
):
    # given
    warehouse_ids = [w.pk for w in warehouses]
    attribute_ids = [attr.pk for attr in Attribute.objects.all()]
    channel_ids = [channel_PLN.pk, channel_USD.pk]
    export_info = {
        "fields": [
            ProductFieldEnum.COLLECTIONS.value,
            ProductFieldEnum.DESCRIPTION.value,
        ],
        "warehouses": warehouse_ids,
        "attributes": attribute_ids,
        "channels": channel_ids,
    }

    expected_file_headers = [
        "id",
        "collections",
        "description",
    ]

    # when
    export_fields, file_headers, data_headers = get_export_fields_and_headers_info(
        export_info
    )

    # then
    expected_fields = [
        "id",
        "collections__slug",
        "description",
    ]

    product_headers = []
    variant_headers = []
    for attr in Attribute.objects.all().order_by("slug"):
        if attr.product_types.exists():
            product_headers.append(f"{attr.slug} (product attribute)")
        if attr.product_variant_types.exists():
            variant_headers.append(f"{attr.slug} (variant attribute)")

    warehouse_headers = [f"{w.slug} (warehouse quantity)" for w in warehouses]

    channel_headers = []
    for channel in Channel.objects.all().order_by("slug"):
        slug = channel.slug
        for field in [
            "product currency code",
            "published",
            "publication date",
            "searchable",
            "available for purchase",
            "price amount",
            "variant currency code",
            "variant cost price",
        ]:
            channel_headers.append(f"{slug} (channel {field})")

    excepted_headers = (
        expected_fields
        + product_headers
        + variant_headers
        + warehouse_headers
        + channel_headers
    )

    expected_file_headers += (
        product_headers + variant_headers + warehouse_headers + channel_headers
    )
    assert expected_file_headers == file_headers
    assert set(export_fields) == set(expected_fields)
    assert data_headers == excepted_headers
