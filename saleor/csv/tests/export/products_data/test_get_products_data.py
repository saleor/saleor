from measurement.measures import Weight

from .....product.models import Attribute, Product, ProductVariant, VariantImage
from .....warehouse.models import Warehouse
from ....utils.products_data import ProductExportFields, get_products_data


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

    variants = []
    for variant in product.variants.all():
        for attr in variant.attributes.all():
            attribute_ids.append(str(attr.assignment.attribute.pk))
        variant.weight = Weight(kg=3)
        variants.append(variant)

    ProductVariant.objects.bulk_update(variants, ["weight"])

    variants = []
    for variant in product_with_image.variants.all():
        variant.weight = None
        variants.append(variant)
    ProductVariant.objects.bulk_update(variants, ["weight"])

    # when
    result_data = get_products_data(
        products, export_fields, attribute_ids, warehouse_ids
    )

    # then
    expected_data = []
    for product in products.order_by("pk"):
        product_data = {
            "id": product.id,
            "name": product.name,
            "is_published": product.is_published,
            "description": product.description,
            "category__slug": product.category.slug,
            "price_amount": product.price_amount,
            "currency": product.currency,
            "product_type__name": product.product_type.name,
            "charge_taxes": product.charge_taxes,
            "collections__slug": (
                ""
                if not product.collections.all()
                else product.collections.first().slug
            ),
            "product_weight": (
                "{} g".format(int(product.weight.value * 1000))
                if product.weight
                else ""
            ),
            "images__image": (
                ""
                if not product.images.all()
                else "http://mirumee.com{}".format(product.images.first().image.url)
            ),
        }

        assigned_attribute = product.attributes.first()
        if assigned_attribute:
            header = f"{assigned_attribute.attribute.slug} (product attribute)"
            product_data[header] = assigned_attribute.values.first().slug

        for variant in product.variants.all():
            data = {
                "variants__sku": variant.sku,
                "variants__currency": variant.currency,
                "variants__price_override_amount": variant.price_override_amount,
                "variants__cost_price_amount": variant.cost_price_amount,
                "variants__images__image": (
                    ""
                    if not variant.images.all()
                    else "http://mirumee.com{}".format(variant.images.first().image.url)
                ),
                "variant_weight": (
                    "{} g".foramt(int(variant.weight.value * 1000))
                    if variant.weight
                    else ""
                ),
            }
            data.update(product_data)

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
    export_fields = {"id", "variants__sku"}
    attribute_ids = [str(attr.pk) for attr in Attribute.objects.all()][:1]

    # when
    result_data = get_products_data(products, export_fields, attribute_ids, [])

    # then
    expected_data = []
    for product in products.order_by("pk"):
        product_data = {"id": product.pk}

        for assigned_attribute in product.attributes.all():
            if assigned_attribute:
                header = f"{assigned_attribute.attribute.slug} (product attribute)"
                if str(assigned_attribute.attribute.pk) in attribute_ids:
                    product_data[header] = assigned_attribute.values.first().slug

        for variant in product.variants.all():
            data = {}
            data.update(product_data)
            data["variants__sku"] = variant.sku
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
    export_fields = {"id", "variants__sku"}
    warehouse_ids = [str(warehouse.pk) for warehouse in Warehouse.objects.all()][:2]
    attribute_ids = []

    # when
    result_data = get_products_data(
        products, export_fields, attribute_ids, warehouse_ids
    )

    # then
    expected_data = []
    for product in products.order_by("pk"):
        product_data = {"id": product.pk}

        for variant in product.variants.all():
            data = {"variants__sku": variant.sku}
            data.update(product_data)

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
    export_fields = {"id", "variants__sku"}
    warehouse_ids = [str(warehouse.pk) for warehouse in Warehouse.objects.all()]
    attribute_ids = [str(attr.pk) for attr in Attribute.objects.all()]

    # when
    result_data = get_products_data(
        products, export_fields, attribute_ids, warehouse_ids
    )

    # then
    expected_data = []
    for product in products.order_by("pk"):
        product_data = {"id": product.id}

        for assigned_attribute in product.attributes.all():
            if assigned_attribute:
                header = f"{assigned_attribute.attribute.slug} (product attribute)"
                if str(assigned_attribute.attribute.pk) in attribute_ids:
                    product_data[header] = assigned_attribute.values.first().slug

        for variant in product.variants.all():
            data = {"variants__sku": variant.sku}
            data.update(product_data)

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
