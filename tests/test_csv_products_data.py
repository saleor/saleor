from measurement.measures import Weight

from saleor.csv.utils.products_data import (
    ProductExportFields,
    add_attribute_info_to_data,
    add_collection_info_to_data,
    add_image_uris_to_data,
    add_warehouse_info_to_data,
    get_attributes_headers,
    get_export_fields_and_headers_info,
    get_product_export_fields_and_headers,
    get_products_data,
    get_warehouses_headers,
    prepare_products_relations_data,
    prepare_variants_data,
)
from saleor.graphql.csv.enums import ProductFieldEnum
from saleor.product.models import Attribute, Product, VariantImage
from saleor.warehouse.models import Warehouse


def test_get_products_data(product, product_with_image, collection, image):
    # given
    product.weight = Weight(kg=5)
    product.save()

    collection.products.add(product)

    variant = product.variants.first()
    VariantImage.objects.create(variant=variant, image=product.images.first())

    products = Product.objects.all()
    export_fields = set(
        value
        for mapping in ProductExportFields.HEADERS_TO_FIELDS_MAPPING.values()
        for value in mapping.values()
    )
    warehouse_ids = [str(warehouse.pk) for warehouse in Warehouse.objects.all()]
    attribute_ids = [str(attr.pk) for attr in Attribute.objects.all()]
    for variant in product.variants.all():
        for attr in variant.attributes.all():
            attribute_ids.append(str(attr.assignment.attribute.pk))

    # when
    result_data = get_products_data(
        products, export_fields, warehouse_ids, attribute_ids
    )

    # then
    expected_data = []
    for product in products.order_by("pk"):
        product_data = {}
        product_data["collections__slug"] = (
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
        product_data["product_weight"] = (
            "{} g".format(int(product.weight.value * 1000)) if product.weight else ""
        )
        product_data["charge_taxes"] = product.charge_taxes
        product_data["product_image_path"] = (
            ""
            if not product.images.all()
            else "http://mirumee.com{}".format(product.images.first().image.url)
        )

        assigned_attribute = product.attributes.first()
        if assigned_attribute:
            header = f"{assigned_attribute.attribute.slug} (product attribute)"
            product_data[header] = assigned_attribute.values.first().slug

        for variant in product.variants.all():
            data = {}
            data.update(product_data)
            data["variant_image_path"] = (
                ""
                if not variant.images.all()
                else "http://mirumee.com{}".format(variant.images.first().image.url)
            )
            data["sku"] = variant.sku
            data["variant_currency"] = variant.currency
            data["price_override_amount"] = variant.price_override_amount
            data["cost_price_amount"] = variant.cost_price_amount
            data["variant_weight"] = (
                "{} g".foramt(int(variant.weight.value * 1000))
                if variant.weight
                else ""
            )

            for stock in variant.stocks.all():
                slug = stock.warehouse.slug
                warehouse_headers = [
                    f"{slug} (warehouse quantity)",
                ]
                data[warehouse_headers[0]] = stock.quantity

            assigned_attribute = variant.attributes.first()
            if assigned_attribute:
                header = f"{assigned_attribute.attribute.slug} (variant attribute)"
                data[header] = assigned_attribute.values.first().slug

            expected_data.append(data)

    assert result_data == expected_data


def test_get_products_data_for_specified_attributes(
    product, product_with_variant_with_two_attributes
):
    # given
    products = Product.objects.all()
    export_fields = {"id", "sku"}
    attribute_ids = [str(attr.pk) for attr in Attribute.objects.all()][:1]

    # when
    result_data = get_products_data(products, export_fields, [], attribute_ids)

    # then
    expected_data = []
    for product in products.order_by("pk"):
        product_data = {}
        product_data["id"] = product.pk

        for assigned_attribute in product.attributes.all():
            if assigned_attribute:
                header = f"{assigned_attribute.attribute.slug} (product attribute)"
                if str(assigned_attribute.attribute.pk) in attribute_ids:
                    product_data[header] = assigned_attribute.values.first().slug

        for variant in product.variants.all():
            data = {}
            data.update(product_data)
            data["sku"] = variant.sku
            for assigned_attribute in variant.attributes.all():
                header = f"{assigned_attribute.attribute.slug} (variant attribute)"
                if str(assigned_attribute.attribute.pk) in attribute_ids:
                    data[header] = assigned_attribute.values.first().slug

            expected_data.append(data)

    assert result_data == expected_data


def test_get_products_data_for_specified_warehouses(
    product, product_with_image, variant_with_many_stocks
):
    # given
    product.variants.add(variant_with_many_stocks)

    products = Product.objects.all()
    export_fields = {"id", "sku"}
    warehouse_ids = [str(warehouse.pk) for warehouse in Warehouse.objects.all()][:2]
    attribute_ids = []

    # when
    result_data = get_products_data(
        products, export_fields, warehouse_ids, attribute_ids
    )

    # then
    expected_data = []
    for product in products.order_by("pk"):
        product_data = {}
        product_data["id"] = product.pk

        for variant in product.variants.all():
            data = {}
            data.update(product_data)
            data["sku"] = variant.sku

            for stock in variant.stocks.all():
                if str(stock.warehouse.pk) in warehouse_ids:
                    slug = stock.warehouse.slug
                    warehouse_headers = [
                        f"{slug} (warehouse quantity)",
                    ]
                    data[warehouse_headers[0]] = stock.quantity

            expected_data.append(data)

    for res in result_data:
        assert res in expected_data


def test_get_products_data_for_specified_warehouses_and_attributes(
    product,
    variant_with_many_stocks,
    product_with_image,
    product_with_variant_with_two_attributes,
):
    # given
    product.variants.add(variant_with_many_stocks)

    products = Product.objects.all()
    export_fields = {"id", "sku"}
    warehouse_ids = [str(warehouse.pk) for warehouse in Warehouse.objects.all()]
    attribute_ids = [str(attr.pk) for attr in Attribute.objects.all()]

    # when
    result_data = get_products_data(
        products, export_fields, warehouse_ids, attribute_ids
    )

    # then
    expected_data = []
    for product in products.order_by("pk"):
        product_data = {}
        product_data["id"] = product.pk

        for assigned_attribute in product.attributes.all():
            if assigned_attribute:
                header = f"{assigned_attribute.attribute.slug} (product attribute)"
                if str(assigned_attribute.attribute.pk) in attribute_ids:
                    product_data[header] = assigned_attribute.values.first().slug

        for variant in product.variants.all():
            data = {}
            data.update(product_data)
            data["sku"] = variant.sku

            for stock in variant.stocks.all():
                if str(stock.warehouse.pk) in warehouse_ids:
                    slug = stock.warehouse.slug
                    warehouse_headers = [
                        f"{slug} (warehouse quantity)",
                    ]
                    data[warehouse_headers[0]] = stock.quantity

            for assigned_attribute in variant.attributes.all():
                header = f"{assigned_attribute.attribute.slug} (variant attribute)"
                if str(assigned_attribute.attribute.pk) in attribute_ids:
                    data[header] = assigned_attribute.values.first().slug

            expected_data.append(data)

    assert result_data == expected_data


def test_prepare_products_relations_data(product_with_image, collection_list):
    # given
    pk = product_with_image.pk
    collection_list[0].products.add(product_with_image)
    collection_list[1].products.add(product_with_image)
    qs = Product.objects.all()
    fields = set(
        ProductExportFields.HEADERS_TO_FIELDS_MAPPING["product_many_to_many"].values()
    )
    attribute_ids = [
        str(attr.assignment.attribute.pk)
        for attr in product_with_image.attributes.all()
    ]

    # when
    result = prepare_products_relations_data(qs, fields, attribute_ids)

    # then
    collections = ", ".join(
        sorted([collection.slug for collection in collection_list[:2]])
    )
    images = ", ".join(
        [
            "http://mirumee.com/media/" + image.image.name
            for image in product_with_image.images.all()
        ]
    )
    expected_result = {
        pk: {"collections__slug": collections, "product_image_path": images}
    }

    assigned_attribute = product_with_image.attributes.first()
    if assigned_attribute:
        header = f"{assigned_attribute.attribute.slug} (product attribute)"
        expected_result[pk][header] = assigned_attribute.values.first().slug

    assert result == expected_result


def test_prepare_variants_data(product):
    # given
    variant = product.variants.first()
    variant.weight = Weight(kg=5)
    variant.save()

    data = {"id": 123, "name": "test_product"}
    variant_fields = set(
        ProductExportFields.HEADERS_TO_FIELDS_MAPPING["variant_fields"].values()
    )
    warhouse_ids = [str(stock.warehouse.pk) for stock in variant.stocks.all()]
    attribute_ids = [
        str(attr.assignment.attribute.pk) for attr in variant.attributes.all()
    ]

    # when
    result_data = prepare_variants_data(
        product.pk, data, variant_fields, warhouse_ids, attribute_ids
    )

    # then
    variant_data = {
        "sku": variant.sku,
        "cost_price_amount": variant.cost_price_amount,
        "price_override_amount": variant.price_override_amount,
        "variant_currency": variant.currency,
        "variant_weight": "{} g".format(int(variant.weight.value * 1000))
        if variant.weight
        else "",
    }
    assigned_attribute = variant.attributes.first()
    if assigned_attribute:
        header = f"{assigned_attribute.attribute.slug} (variant attribute)"
        variant_data[header] = assigned_attribute.values.first().slug

    for stock in variant.stocks.all():
        slug = stock.warehouse.slug
        headers = [
            f"{slug} (warehouse quantity)",
        ]
        variant_data[headers[0]] = stock.quantity

    expected_result = {**data, **variant_data}

    assert result_data == [expected_result]


def test_add_collection_info_to_data(product):
    # given
    pk = product.pk
    collection = "test_collection"
    input_data = {pk: {}}

    # when
    result = add_collection_info_to_data(product.pk, collection, input_data)

    # then
    assert result[pk]["collections__slug"] == {collection}


def test_add_collection_info_to_data_update_collections(product):
    # given
    pk = product.pk
    existing_collection = "test2"
    collection = "test_collection"
    input_data = {pk: {"collections__slug": {existing_collection}}}

    # when
    result = add_collection_info_to_data(product.pk, collection, input_data)

    # then
    assert result[pk]["collections__slug"] == {collection, existing_collection}


def test_add_collection_info_to_data_no_collection(product):
    # given
    pk = product.pk
    collection = None
    input_data = {pk: {}}

    # when
    result = add_collection_info_to_data(product.pk, collection, input_data)

    # then
    assert result == input_data


def test_add_image_uris_to_data(product):
    # given
    pk = product.pk
    image_path = "test/path/image.jpg"
    field = "variant_images"
    input_data = {pk: {}}

    # when
    result = add_image_uris_to_data(product.pk, image_path, field, input_data)

    # then
    assert result[pk][field] == {"http://mirumee.com/media/" + image_path}


def test_add_image_uris_to_data_update_images(product):
    # given
    pk = product.pk
    old_path = "http://mirumee.com/media/test/image0.jpg"
    image_path = "test/path/image.jpg"
    input_data = {pk: {"product_images": {old_path}}}
    field = "product_images"

    # when
    result = add_image_uris_to_data(product.pk, image_path, field, input_data)

    # then
    assert result[pk][field] == {"http://mirumee.com/media/" + image_path, old_path}


def test_add_image_uris_to_data_no_image_path(product):
    # given
    pk = product.pk
    image_path = None
    input_data = {pk: {"name": "test"}}

    # when
    result = add_image_uris_to_data(
        product.pk, image_path, "product_images", input_data
    )

    # then
    assert result == input_data


def test_add_attribute_info_to_data(product):
    # given
    pk = product.pk
    slug = "test_attribute_slug"
    value = "test value"
    attribute_data = {
        "slug": slug,
        "value": value,
    }
    input_data = {pk: {}}

    # when
    result = add_attribute_info_to_data(
        product.pk, attribute_data, "product attribute", input_data
    )

    # then
    expected_header = f"{slug} (product attribute)"
    assert result[pk][expected_header] == {value}


def test_add_attribute_info_to_data_update_attribute_data(product):
    # given
    pk = product.pk
    slug = "test_attribute_slug"
    value = "test value"
    expected_header = f"{slug} (variant attribute)"

    attribute_data = {
        "slug": slug,
        "value": value,
    }
    input_data = {pk: {expected_header: {"value1"}}}

    # when
    result = add_attribute_info_to_data(
        product.pk, attribute_data, "variant attribute", input_data
    )

    # then
    assert result[pk][expected_header] == {value, "value1"}


def test_add_attribute_info_to_data_no_slug(product):
    # given
    pk = product.pk
    attribute_data = {
        "slug": None,
        "value": None,
    }
    input_data = {pk: {}}

    # when
    result = add_attribute_info_to_data(
        product.pk, attribute_data, "variant attribute", input_data
    )

    # then
    assert result == input_data


def test_add_warehouse_info_to_data(product):
    # given
    pk = product.pk
    slug = "test_warehouse"
    warehouse_data = {
        "slug": slug,
        "qty": 12,
        "qty_alc": 10,
    }
    input_data = {pk: {}}

    # when
    result = add_warehouse_info_to_data(product.pk, warehouse_data, input_data)

    # then
    expected_header = f"{slug} (warehouse quantity)"
    assert result[pk][expected_header] == 12


def test_add_warehouse_info_to_data_data_not_changed(product):
    # given
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

    # when
    result = add_warehouse_info_to_data(product.pk, warehouse_data, input_data)

    # then
    assert result == input_data


def test_add_warehouse_info_to_data_data_no_slug(product):
    # given
    pk = product.pk
    warehouse_data = {
        "slug": None,
        "qty": None,
        "qty_alc": None,
    }
    input_data = {pk: {}}

    # when
    result = add_warehouse_info_to_data(product.pk, warehouse_data, input_data)

    # then
    assert result == input_data


def test_get_export_fields_and_headers_fields_with_price():
    # given
    export_info = {
        "fields": [
            ProductFieldEnum.PRICE.value,
            ProductFieldEnum.PRICE_OVERRIDE.value,
            ProductFieldEnum.COLLECTIONS.value,
            ProductFieldEnum.DESCRIPTION.value,
        ],
        "warehoses": [],
    }

    # when
    export_fields, csv_headers_mapping = get_product_export_fields_and_headers(
        export_info
    )

    # then
    expected_mapping = {
        "price_amount": "price",
        "product_currency": "product currency",
        "price_override_amount": "price override",
        "variant_currency": "variant currency",
        "collections__slug": "collections",
        "description": "description",
    }

    expected_fields = set(expected_mapping.keys())
    expected_fields.add("id")

    assert set(export_fields) == expected_fields
    assert csv_headers_mapping == expected_mapping


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
    export_fields, csv_headers_mapping = get_product_export_fields_and_headers(
        export_info
    )

    # then
    expected_mapping = {
        "collections__slug": "collections",
        "description": "description",
        "sku": "variant sku",
    }

    assert set(export_fields) == {"collections__slug", "id", "sku", "description"}
    assert csv_headers_mapping == expected_mapping


def test_get_export_fields_and_headers_no_fields():
    export_fields, csv_headers_mapping = get_product_export_fields_and_headers({})

    assert export_fields == ["id"]
    assert csv_headers_mapping == {}


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


def test_get_export_fields_and_headers_info(
    warehouses, product_with_multiple_values_attributes
):
    # given
    warehouse_ids = [w.pk for w in warehouses]
    attribute_ids = [attr.pk for attr in Attribute.objects.all()]
    export_info = {
        "fields": [
            ProductFieldEnum.PRICE.value,
            ProductFieldEnum.PRICE_OVERRIDE.value,
            ProductFieldEnum.COLLECTIONS.value,
            ProductFieldEnum.DESCRIPTION.value,
        ],
        "warehouses": warehouse_ids,
        "attributes": attribute_ids,
    }

    expected_mapping = {
        "price_amount": "price",
        "product_currency": "product currency",
        "price_override_amount": "price override",
        "variant_currency": "variant currency",
        "collections__slug": "collections",
        "description": "description",
    }

    # when
    export_fields, csv_headers_mapping, headers = get_export_fields_and_headers_info(
        export_info
    )

    # then
    expected_fields = set(expected_mapping.keys())
    expected_fields.add("id")

    product_headers = []
    variant_headers = []
    for attr in Attribute.objects.all():
        if attr.product_types.exists():
            product_headers.append(f"{attr.slug} (product attribute)")
        if attr.product_variant_types.exists():
            variant_headers.append(f"{attr.slug} (variant attribute)")

    warehouse_headers = [f"{w.slug} (warehouse quantity)" for w in warehouses]
    excepted_headers = (
        ["id"]
        + list(expected_fields)
        + product_headers
        + variant_headers
        + warehouse_headers
    )

    assert expected_mapping == csv_headers_mapping
    assert set(export_fields) == expected_fields
    assert set(headers) == set(excepted_headers)
