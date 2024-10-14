import datetime

import pytest

from ....attribute.utils import associate_attribute_values_to_instance
from ...models import Category, Product, ProductChannelListing


@pytest.fixture
def category_generator():
    def create_category(
        name="Default",
        slug="default",
    ):
        category = Category.objects.create(
            name=name,
            slug=slug,
        )
        return category

    return create_category


@pytest.fixture
def category(category_generator):  # pylint: disable=W0613
    return category_generator()


@pytest.fixture
def category_with_image(db, image, media_root):  # pylint: disable=W0613
    return Category.objects.create(
        name="Default2", slug="default2", background_image=image
    )


@pytest.fixture
def categories(db):
    category1 = Category.objects.create(name="Category1", slug="cat1")
    category2 = Category.objects.create(name="Category2", slug="cat2")
    return [category1, category2]


@pytest.fixture
def category_list():
    category_1 = Category.objects.create(name="Category 1", slug="category-1")
    category_2 = Category.objects.create(name="Category 2", slug="category-2")
    category_3 = Category.objects.create(name="Category 3", slug="category-3")
    return category_1, category_2, category_3


@pytest.fixture
def categories_tree(db, product_type, channel_USD):  # pylint: disable=W0613
    parent = Category.objects.create(name="Parent", slug="parent")
    parent.children.create(name="Child", slug="child")
    child = parent.children.first()

    product_attr = product_type.product_attributes.first()
    attr_value = product_attr.values.first()

    product = Product.objects.create(
        name="Test product",
        slug="test-product-10",
        product_type=product_type,
        category=child,
    )
    ProductChannelListing.objects.create(
        product=product,
        channel=channel_USD,
        is_published=True,
        visible_in_listings=True,
    )

    associate_attribute_values_to_instance(product, {product_attr.pk: [attr_value]})
    return parent


@pytest.fixture
def categories_tree_with_published_products(
    categories_tree, product, channel_USD, channel_PLN
):
    parent = categories_tree
    parent_product = product
    parent_product.category = parent

    child = parent.children.first()
    child_product = child.products.first()

    product_list = [child_product, parent_product]

    ProductChannelListing.objects.filter(product__in=product_list).delete()
    product_channel_listings = []
    for product in product_list:
        product.save()
        product_channel_listings.append(
            ProductChannelListing(
                product=product,
                channel=channel_USD,
                published_at=datetime.datetime.now(tz=datetime.UTC),
                is_published=True,
            )
        )
        product_channel_listings.append(
            ProductChannelListing(
                product=product,
                channel=channel_PLN,
                published_at=datetime.datetime.now(tz=datetime.UTC),
                is_published=True,
            )
        )
    ProductChannelListing.objects.bulk_create(product_channel_listings)
    return parent


@pytest.fixture
def non_default_category(db):  # pylint: disable=W0613
    return Category.objects.create(name="Not default", slug="not-default")


@pytest.fixture
def category_with_products(
    categories_tree,
    category,
    product_with_image,
    product_list_published,
    product_with_variant_with_two_attributes,
    product_with_multiple_values_attributes,
    product_without_shipping,
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
