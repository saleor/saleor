import pytest

from .....discount.models import Sale, SaleChannelListing
from .....product.models import Category


@pytest.fixture
def sales_list(channel_USD):
    sales = Sale.objects.bulk_create([Sale(name="Sale1"), Sale(name="Sale2")])
    values = [15, 5]
    SaleChannelListing.objects.bulk_create(
        [
            SaleChannelListing(
                sale=sale,
                channel=channel_USD,
                discount_value=values[i],
                currency=channel_USD.currency_code,
            )
            for i, sale in enumerate(sales)
        ]
    )
    return list(sales)


@pytest.fixture
def category_with_products(
    categories_tree,
    category,
    product_with_image,
    product_list_published,
    product_with_variant_with_two_attributes,
    product_with_multiple_values_attributes,
    product_without_shipping,
    sales_list,
):
    category = categories_tree
    child = Category.objects.create(name="TestCategory", slug="test-cat")
    child_2 = Category.objects.create(name="TestCategory2", slug="test-cat2")
    category.children.add(child, child_2)

    product_list_published.update(category=category)

    product_with_image.category = category
    product_with_image.save()
    product_with_variant_with_two_attributes.category = category
    product_with_variant_with_two_attributes.save()
    product_with_multiple_values_attributes.category = category
    product_with_multiple_values_attributes.save()
    product_without_shipping.category = category
    product_without_shipping.save()

    return category


@pytest.fixture
def categories_with_children(db):
    categories = Category.tree.build_tree_nodes(
        {
            "id": 1,
            "name": "Category1",
            "slug": "cat1",
            "children": [
                {
                    "id": 4,
                    "parent_id": 1,
                    "name": "Category4",
                    "slug": "cat4",
                    "children": [
                        {
                            "parent_id": 4,
                            "id": 14,
                            "name": "Category4A",
                            "slug": "cat4A",
                        },
                        {
                            "parent_id": 4,
                            "id": 18,
                            "name": "Category4B",
                            "slug": "cat4B",
                        },
                    ],
                },
                {
                    "id": 5,
                    "parent_id": 1,
                    "name": "Category5",
                    "slug": "cat5",
                    "children": [
                        {
                            "parent_id": 5,
                            "id": 15,
                            "name": "Category5A",
                            "slug": "cat5A",
                        },
                        {
                            "parent_id": 5,
                            "id": 19,
                            "name": "Category5B",
                            "slug": "cat5B",
                        },
                    ],
                },
                {
                    "id": 6,
                    "parent_id": 1,
                    "name": "Category6",
                    "slug": "cat6",
                    "children": [
                        {
                            "parent_id": 6,
                            "id": 16,
                            "name": "Category6A",
                            "slug": "cat6A",
                        },
                        {
                            "parent_id": 6,
                            "id": 20,
                            "name": "Category6B",
                            "slug": "cat6B",
                        },
                    ],
                },
                {
                    "id": 7,
                    "parent_id": 1,
                    "name": "Category7",
                    "slug": "cat7",
                    "children": [
                        {
                            "parent_id": 7,
                            "id": 17,
                            "name": "Category7A",
                            "slug": "cat7A",
                        },
                        {
                            "parent_id": 7,
                            "id": 21,
                            "name": "Category7B",
                            "slug": "cat7B",
                        },
                        {
                            "parent_id": 7,
                            "id": 22,
                            "name": "Category7C",
                            "slug": "cat7C",
                        },
                    ],
                },
            ],
        }
    )
    categories.extend(
        Category.tree.build_tree_nodes(
            {
                "id": 2,
                "name": "Category2",
                "slug": "cat2",
                "children": [
                    {
                        "id": 8,
                        "parent_id": 2,
                        "name": "Category8",
                        "slug": "cat8",
                        "children": [
                            {
                                "parent_id": 8,
                                "id": 23,
                                "name": "Category8A",
                                "slug": "cat8A",
                            },
                            {
                                "parent_id": 8,
                                "id": 27,
                                "name": "Category8B",
                                "slug": "cat8B",
                            },
                        ],
                    },
                    {
                        "id": 9,
                        "parent_id": 2,
                        "name": "Category9",
                        "slug": "cat9",
                        "children": [
                            {
                                "parent_id": 9,
                                "id": 24,
                                "name": "Category9A",
                                "slug": "cat9A",
                            },
                            {
                                "parent_id": 9,
                                "id": 28,
                                "name": "Category9B",
                                "slug": "cat9B",
                            },
                        ],
                    },
                    {
                        "id": 10,
                        "parent_id": 2,
                        "name": "Category10",
                        "slug": "cat10",
                        "children": [
                            {
                                "parent_id": 10,
                                "id": 25,
                                "name": "Category10A",
                                "slug": "cat10A",
                            },
                            {
                                "parent_id": 10,
                                "id": 29,
                                "name": "Category10B",
                                "slug": "cat10B",
                            },
                        ],
                    },
                    {
                        "id": 11,
                        "parent_id": 2,
                        "name": "Category11",
                        "slug": "cat11",
                        "children": [
                            {
                                "parent_id": 11,
                                "id": 26,
                                "name": "Category11A",
                                "slug": "cat11A",
                            },
                            {
                                "parent_id": 11,
                                "id": 30,
                                "name": "Category11B",
                                "slug": "cat11B",
                            },
                            {
                                "parent_id": 11,
                                "id": 31,
                                "name": "Category11C",
                                "slug": "cat11C",
                            },
                        ],
                    },
                ],
            }
        )
    )
    categories = Category.objects.bulk_create(categories)
    return categories
