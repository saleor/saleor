import datetime

import graphene
import pytest
from django.utils import timezone
from freezegun import freeze_time

from .....product.models import ProductVariant
from ....tests.utils import get_graphql_content

PRODUCT_VARIANTS_WHERE_QUERY = """
    query($where: ProductVariantWhereInput!, $channel: String) {
      productVariants(first: 10, where: $where, channel: $channel) {
        edges {
          node {
            id
            name
            sku
          }
        }
      }
    }
"""


def test_product_variant_filter_by_ids(api_client, product_variant_list, channel_USD):
    # given
    ids = [
        graphene.Node.to_global_id("ProductVariant", variant.pk)
        for variant in product_variant_list[:2]
    ]
    variables = {"channel": channel_USD.slug, "where": {"AND": [{"ids": ids}]}}

    # when
    response = api_client.post_graphql(PRODUCT_VARIANTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    variants = data["data"]["productVariants"]["edges"]
    assert len(variants) == 2
    returned_slugs = {node["node"]["sku"] for node in variants}
    assert returned_slugs == {
        product_variant_list[0].sku,
        product_variant_list[1].sku,
    }


def test_product_variant_filter_by_none_as_ids(
    api_client, product_variant_list, channel_USD
):
    # given
    variables = {"channel": channel_USD.slug, "where": {"AND": [{"ids": None}]}}

    # when
    response = api_client.post_graphql(PRODUCT_VARIANTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    variants = data["data"]["productVariants"]["edges"]
    assert len(variants) == 0


def test_product_variant_filter_by_ids_empty_list(
    api_client, product_variant_list, channel_USD
):
    # given
    variables = {"channel": channel_USD.slug, "where": {"AND": [{"ids": []}]}}

    # when
    response = api_client.post_graphql(PRODUCT_VARIANTS_WHERE_QUERY, variables)

    # then
    data = get_graphql_content(response)
    variants = data["data"]["productVariants"]["edges"]
    assert len(variants) == 0


@pytest.mark.parametrize(
    ("where", "indexes"),
    [
        (
            {
                "gte": (timezone.now() - datetime.timedelta(days=25)).isoformat(),
                "lte": (timezone.now() - datetime.timedelta(days=2)).isoformat(),
            },
            [0, 1],
        ),
        (
            {
                "lte": (timezone.now() - datetime.timedelta(days=25)).isoformat(),
            },
            [],
        ),
        (
            {
                "lte": (timezone.now() - datetime.timedelta(hours=10)).isoformat(),
            },
            [0, 1],
        ),
        (None, []),
        ({"gte": None}, []),
        ({"lte": None}, []),
        ({"lte": None, "gte": None}, []),
        ({}, []),
    ],
)
def test_product_variant_filter_by_updated_at(
    where,
    indexes,
    product_variant_list,
    api_client,
    channel_USD,
):
    # given
    with freeze_time((timezone.now() - datetime.timedelta(days=15)).isoformat()):
        product_variant_list[0].save(update_fields=["updated_at"])

    with freeze_time((timezone.now() - datetime.timedelta(days=3)).isoformat()):
        product_variant_list[1].save(update_fields=["updated_at"])

    # variant available only in channel PLN
    with freeze_time((timezone.now() - datetime.timedelta(days=1)).isoformat()):
        product_variant_list[2].save(update_fields=["updated_at"])

    variables = {"channel": channel_USD.slug, "where": {"updatedAt": where}}

    # when
    response = api_client.post_graphql(PRODUCT_VARIANTS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    variants = content["data"]["productVariants"]["edges"]
    assert len(variants) == len(indexes)
    skus = {node["node"]["sku"] for node in variants}
    assert skus == {product_variant_list[index].sku for index in indexes}


@pytest.mark.parametrize(
    ("where", "indexes"),
    [
        ({"eq": "SKU1"}, [0]),
        ({"eq": "SKU2"}, [1]),
        ({"eq": "SKU_NON_EXISTENT"}, []),
        ({"oneOf": ["SKU1", "SKU2"]}, [0, 1]),
        ({"oneOf": ["SKU1", "SKU_NON_EXISTENT"]}, [0]),
        ({"oneOf": []}, []),
        (None, []),
        ({}, []),
    ],
)
def test_product_variant_filter_by_sku(
    where,
    indexes,
    product_variant_list,
    api_client,
    channel_USD,
):
    # given
    product_variant_list[0].sku = "SKU1"
    product_variant_list[1].sku = "SKU2"
    product_variant_list[2].sku = "SKU3"
    ProductVariant.objects.bulk_update(product_variant_list, ["sku"])

    variables = {"channel": channel_USD.slug, "where": {"sku": where}}

    # when
    response = api_client.post_graphql(PRODUCT_VARIANTS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    variants = content["data"]["productVariants"]["edges"]
    assert len(variants) == len(indexes)
    skus = {node["node"]["sku"] for node in variants}
    assert skus == {product_variant_list[index].sku for index in indexes}


VARIANT_A_EXTERNAL_REFERENCE = "external-reference-a"
VARIANT_B_EXTERNAL_REFERENCE = "external-reference-b"


@pytest.mark.parametrize(
    ("_case", "where", "indexes"),
    [
        ("eq_match", {"eq": VARIANT_A_EXTERNAL_REFERENCE}, [0]),
        ("eq_no_match", {"eq": "non-existing"}, []),
        ("eq_empty_string", {"eq": ""}, []),
        ("eq_null_matches_variants_without_reference", {"eq": None}, [3]),
        (
            "one_of_multiple_matches",
            {"oneOf": [VARIANT_A_EXTERNAL_REFERENCE, VARIANT_B_EXTERNAL_REFERENCE]},
            [0, 1],
        ),
        (
            "one_of_mixed_existing_and_non_existing",
            {"oneOf": [VARIANT_B_EXTERNAL_REFERENCE, "non-existing"]},
            [1],
        ),
        ("one_of_no_match", {"oneOf": ["non-existing-1", "non-existing-2"]}, []),
        ("one_of_empty_list", {"oneOf": []}, []),
        ("one_of_null", {"oneOf": None}, []),
        ("empty_input", {}, []),
        ("null_input", None, []),
    ],
)
def test_product_variant_filter_by_external_reference(
    _case, where, indexes, api_client, product_variant_list, channel_USD
):
    # given
    ProductVariant.objects.exclude(
        pk__in=[variant.pk for variant in product_variant_list]
    ).delete()
    product_variant_list[0].external_reference = VARIANT_A_EXTERNAL_REFERENCE
    product_variant_list[1].external_reference = VARIANT_B_EXTERNAL_REFERENCE
    ProductVariant.objects.bulk_update(product_variant_list[:2], ["external_reference"])
    assert product_variant_list[3].external_reference is None

    variables = {"channel": channel_USD.slug, "where": {"externalReference": where}}

    # when
    response = api_client.post_graphql(PRODUCT_VARIANTS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    variants = content["data"]["productVariants"]["edges"]
    assert len(variants) == len(indexes)
    returned_ids = {node["node"]["id"] for node in variants}
    assert returned_ids == {
        graphene.Node.to_global_id("ProductVariant", product_variant_list[index].pk)
        for index in indexes
    }


def test_product_variant_filter_by_external_reference_and_sku(
    api_client, product_variant_list, channel_USD
):
    # given
    product_variant_list[0].external_reference = VARIANT_A_EXTERNAL_REFERENCE
    product_variant_list[1].external_reference = VARIANT_B_EXTERNAL_REFERENCE
    ProductVariant.objects.bulk_update(product_variant_list[:2], ["external_reference"])
    expected_variant = product_variant_list[1]

    variables = {
        "channel": channel_USD.slug,
        "where": {
            "AND": [
                {
                    "externalReference": {
                        "oneOf": [
                            VARIANT_A_EXTERNAL_REFERENCE,
                            VARIANT_B_EXTERNAL_REFERENCE,
                        ]
                    }
                },
                {"sku": {"eq": expected_variant.sku}},
            ]
        },
    }

    # when
    response = api_client.post_graphql(PRODUCT_VARIANTS_WHERE_QUERY, variables)

    # then
    content = get_graphql_content(response)
    variants = content["data"]["productVariants"]["edges"]
    assert len(variants) == 1
    assert variants[0]["node"]["id"] == graphene.Node.to_global_id(
        "ProductVariant", expected_variant.pk
    )
