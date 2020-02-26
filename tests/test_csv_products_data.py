from unittest.mock import patch

from saleor.csv.utils.products_data import (
    ProductExportFields,
    add_attribute_info_to_data,
    add_collection_info_to_data,
    add_image_uris_to_data,
    add_warehouse_info_to_data,
    get_products_data,
    prepare_product_relations_data,
    prepare_products_data,
    prepare_variants_data,
)
from saleor.product.models import Product, VariantImage


@patch("saleor.csv.utils.products_data.prepare_products_data")
def test_get_products_data(mock_prepare_products_data, product_list):
    exp_data = [{"test1": "test"}]
    attr_and_warehouse_headers = ["attr1", "test warehouse", "attr2"]
    mock_prepare_products_data.return_value = (exp_data, attr_and_warehouse_headers)
    queryset = Product.objects.all()
    export_data, csv_headers_mapping, headers = get_products_data(queryset)

    product_headers = ProductExportFields.PRODUCT_HEADERS_MAPPING
    expected_csv_headers = {
        **product_headers["product"],
        **product_headers["product_many_to_many"],
        **product_headers["variant"],
        **product_headers["common"],
    }
    expected_headers = list(expected_csv_headers.keys()) + attr_and_warehouse_headers

    assert export_data == exp_data
    assert csv_headers_mapping == expected_csv_headers
    assert headers == expected_headers


def test_prepare_products_data(product, product_with_image, collection, image):
    collection.products.add(product)

    variant = product.variants.first()
    VariantImage.objects.create(variant=variant, image=product.images.first())

    products = Product.objects.all()
    data, headers = prepare_products_data(products)

    expected_data = []
    expected_headers = set()
    for product in products.order_by("pk"):
        product_data = {}
        product_data["collections"] = (
            "" if not product.collections.all() else product.collections.first().slug
        )
        product_data["name"] = product.name
        product_data["is_published"] = product.is_published
        product_data["description"] = product.description
        product_data["category__slug"] = product.category.slug
        product_data["price_amount"] = product.price_amount
        product_data["product_currency"] = product.currency
        product_data["product_type__name"] = product.product_type.name
        product_data["id"] = product.pk
        product_data["images"] = (
            ""
            if not product.images.all()
            else "http://mirumee.com{}".format(product.images.first().image.url)
        )

        assigned_attribute = product.attributes.first()
        if assigned_attribute:
            header = f"{assigned_attribute.attribute.slug} (attribute)"
            product_data[header] = assigned_attribute.values.first().slug
            expected_headers.add(header)

        expected_data.append(product_data)

        for variant in product.variants.all():
            variant_data = {}
            variant_data["images"] = (
                ""
                if not variant.images.all()
                else "http://mirumee.com{}".format(variant.images.first().image.url)
            )
            variant_data["sku"] = variant.sku
            variant_data["variant_currency"] = variant.currency
            variant_data["price_override_amount"] = variant.price_override_amount
            variant_data["cost_price_amount"] = variant.cost_price_amount

            for stock in variant.stock.all():
                slug = stock.warehouse.slug
                warehouse_headers = [
                    f"{slug} (warehouse quantity allocated)",
                    f"{slug} (warehouse quantity)",
                ]
                variant_data[warehouse_headers[0]] = stock.quantity_allocated
                variant_data[warehouse_headers[1]] = stock.quantity
                expected_headers.update(warehouse_headers)

            assigned_attribute = variant.attributes.first()
            if assigned_attribute:
                header = f"{assigned_attribute.attribute.slug} (attribute)"
                variant_data[header] = assigned_attribute.values.first().slug
                expected_headers.add(header)

            expected_data.append(variant_data)

    assert data == expected_data
    assert set(headers) == expected_headers


def test_prepare_product_relations_data(product_with_image, collection_list):
    pk = product_with_image.pk
    collection_list[0].products.add(product_with_image)
    collection_list[1].products.add(product_with_image)
    qs = Product.objects.all()
    result, result_headers = prepare_product_relations_data(qs)

    collections = ", ".join(
        sorted([collection.slug for collection in collection_list[:2]])
    )
    images = ", ".join(
        [
            "http://mirumee.com/media/" + image.image.name
            for image in product_with_image.images.all()
        ]
    )
    expected_result = {pk: {"collections": collections, "images": images}}

    assigned_attribute = product_with_image.attributes.first()
    if assigned_attribute:
        header = f"{assigned_attribute.attribute.slug} (attribute)"
        expected_result[pk][header] = assigned_attribute.values.first().slug

    assert result == expected_result


def test_prepare_variants_data(product):
    variant = product.variants.first()

    warehouse_headers = set()
    attribute_headers = set()

    expected_result = {
        "sku": variant.sku,
        "cost_price_amount": variant.cost_price_amount,
        "price_override_amount": variant.price_override_amount,
        "variant_currency": variant.currency,
    }
    assigned_attribute = variant.attributes.first()
    if assigned_attribute:
        header = f"{assigned_attribute.attribute.slug} (attribute)"
        expected_result[header] = assigned_attribute.values.first().slug
        attribute_headers.add(header)

    stock = variant.stock
    for stock in variant.stock.all():
        slug = stock.warehouse.slug
        headers = [
            f"{slug} (warehouse quantity allocated)",
            f"{slug} (warehouse quantity)",
        ]
        expected_result[headers[0]] = stock.quantity_allocated
        expected_result[headers[1]] = stock.quantity
        warehouse_headers.update(headers)

    result_data, res_attribute_headers, res_warehouse_headers = prepare_variants_data(
        product.pk
    )

    assert result_data == [expected_result]
    assert res_attribute_headers == attribute_headers
    assert res_warehouse_headers == warehouse_headers


def test_add_collection_info_to_data(product):
    pk = product.pk
    collection = "test_collection"
    input_data = {pk: {}}
    result = add_collection_info_to_data(product.pk, collection, input_data)

    assert result[pk]["collections"] == {collection}


def test_add_collection_info_to_data_update_collections(product):
    pk = product.pk
    existing_collection = "test2"
    collection = "test_collection"
    input_data = {pk: {"collections": {existing_collection}}}
    result = add_collection_info_to_data(product.pk, collection, input_data)

    assert result[pk]["collections"] == {collection, existing_collection}


def test_add_collection_info_to_data_no_collection(product):
    pk = product.pk
    collection = None
    input_data = {pk: {}}
    result = add_collection_info_to_data(product.pk, collection, input_data)

    assert result == input_data


def test_add_image_uris_to_data(product):
    pk = product.pk
    image_path = "test/path/image.jpg"
    input_data = {pk: {}}
    result = add_image_uris_to_data(product.pk, image_path, input_data)

    assert result[pk]["images"] == {"http://mirumee.com/media/" + image_path}


def test_add_image_uris_to_data_update_images(product):
    pk = product.pk
    old_path = "http://mirumee.com/media/test/image0.jpg"
    image_path = "test/path/image.jpg"
    input_data = {pk: {"images": {old_path}}}
    result = add_image_uris_to_data(product.pk, image_path, input_data)

    assert result[pk]["images"] == {"http://mirumee.com/media/" + image_path, old_path}


def test_add_image_uris_to_data_no_image_path(product):
    pk = product.pk
    image_path = None
    input_data = {pk: {"name": "test"}}
    result = add_image_uris_to_data(product.pk, image_path, input_data)

    assert result == input_data


def test_add_attribute_info_to_data(product):
    pk = product.pk
    slug = "test_attribute_slug"
    value = "test value"
    attribute_data = {
        "slug": slug,
        "value": value,
    }
    input_data = {pk: {}}
    result, header = add_attribute_info_to_data(product.pk, attribute_data, input_data)

    expected_header = f"{slug} (attribute)"

    assert header == expected_header
    assert result[pk][header] == {value}


def test_add_attribute_info_to_data_update_attribute_data(product):
    pk = product.pk
    slug = "test_attribute_slug"
    value = "test value"
    expected_header = f"{slug} (attribute)"

    attribute_data = {
        "slug": slug,
        "value": value,
    }
    input_data = {pk: {expected_header: {"value1"}}}
    result, header = add_attribute_info_to_data(product.pk, attribute_data, input_data)

    assert header == expected_header
    assert result[pk][header] == {value, "value1"}


def test_add_attribute_info_to_data_no_slug(product):
    pk = product.pk
    attribute_data = {
        "slug": None,
        "value": None,
    }
    input_data = {pk: {}}
    result, header = add_attribute_info_to_data(product.pk, attribute_data, input_data)

    assert not header
    assert result == input_data


def test_add_warehouse_info_to_data(product):
    pk = product.pk
    slug = "test_warehouse"
    warehouse_data = {
        "slug": slug,
        "qty": 12,
        "qty_alc": 10,
    }
    input_data = {pk: {}}
    result, headers = add_warehouse_info_to_data(product.pk, warehouse_data, input_data)

    expected_headers = [
        f"{slug} (warehouse quantity)",
        f"{slug} (warehouse quantity allocated)",
    ]
    assert result[pk][expected_headers[0]] == 12
    assert result[pk][expected_headers[1]] == 10
    assert headers == set(expected_headers)


def test_add_warehouse_info_to_data_data_not_changed(product):
    pk = product.pk
    slug = "test_warehouse"
    warehouse_data = {
        "slug": slug,
        "qty": 12,
        "qty_alc": 10,
    }
    input_data = {
        pk: {
            f"{slug} (warehouse quantity)": 5,
            f"{slug} (warehouse quantity allocated)": 8,
        }
    }
    result, headers = add_warehouse_info_to_data(product.pk, warehouse_data, input_data)

    assert result == input_data
    assert headers == set()


def test_add_warehouse_info_to_data_data_no_slug(product):
    pk = product.pk
    warehouse_data = {
        "slug": None,
        "qty": None,
        "qty_alc": None,
    }
    input_data = {pk: {}}
    result, headers = add_warehouse_info_to_data(product.pk, warehouse_data, input_data)

    assert result == input_data
    assert headers == set()
