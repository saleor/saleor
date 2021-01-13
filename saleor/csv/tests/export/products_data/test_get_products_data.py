from measurement.measures import Weight

from .....attribute.models import Attribute, AttributeValue
from .....attribute.utils import associate_attribute_values_to_instance
from .....channel.models import Channel
from .....product.models import Product, ProductVariant, VariantImage
from .....warehouse.models import Warehouse
from ....utils import ProductExportFields
from ....utils.products_data import get_products_data
from .utils import (
    add_channel_to_expected_product_data,
    add_channel_to_expected_variant_data,
    add_product_attribute_data_to_expected_data,
    add_stocks_to_expected_data,
    add_variant_attribute_data_to_expected_data,
)


def test_get_products_data(product, product_with_image, collection, image, channel_USD):
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
    channel_ids = [str(channel.pk) for channel in Channel.objects.all()]

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
        products, export_fields, attribute_ids, warehouse_ids, channel_ids
    )

    # then
    expected_data = []
    for product in products.order_by("pk"):
        product_data = {
            "id": product.id,
            "name": product.name,
            "description": product.description,
            "category__slug": product.category.slug,
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

        product_data = add_product_attribute_data_to_expected_data(
            product_data, product, attribute_ids
        )
        product_data = add_channel_to_expected_product_data(
            product_data, product, channel_ids
        )

        for variant in product.variants.all():
            data = {
                "variants__sku": variant.sku,
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

            data = add_stocks_to_expected_data(data, variant, warehouse_ids)
            data = add_variant_attribute_data_to_expected_data(
                data, variant, attribute_ids
            )
            data = add_channel_to_expected_variant_data(data, variant, channel_ids)

            expected_data.append(data)
    assert result_data == expected_data


def test_get_products_data_for_specified_attributes(
    product, product_with_variant_with_two_attributes
):
    # given
    products = Product.objects.all()
    export_fields = {"id", "variants__sku"}
    attribute_ids = [str(attr.pk) for attr in Attribute.objects.all()][:1]
    warehouse_ids = []
    channel_ids = []

    # when
    result_data = get_products_data(
        products, export_fields, attribute_ids, warehouse_ids, channel_ids
    )

    # then
    expected_data = []
    for product in products.order_by("pk"):
        product_data = {"id": product.pk}

        product_data = add_product_attribute_data_to_expected_data(
            product_data, product, attribute_ids
        )

        for variant in product.variants.all():
            data = {}
            data.update(product_data)
            data["variants__sku"] = variant.sku
            data = add_variant_attribute_data_to_expected_data(
                data, variant, attribute_ids
            )

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
    channel_ids = []

    # when
    result_data = get_products_data(
        products, export_fields, attribute_ids, warehouse_ids, channel_ids
    )

    # then
    expected_data = []
    for product in products.order_by("pk"):
        product_data = {"id": product.pk}

        for variant in product.variants.all():
            data = {"variants__sku": variant.sku}
            data.update(product_data)

            data = add_stocks_to_expected_data(data, variant, warehouse_ids)

            expected_data.append(data)
    for res in result_data:
        assert res in expected_data


def test_get_products_data_for_product_without_channel(
    product, product_with_image, variant_with_many_stocks
):
    # given
    product.variants.add(variant_with_many_stocks)
    product_with_image.channel_listings.all().delete()

    products = Product.objects.all()
    export_fields = {"id", "variants__sku"}
    warehouse_ids = []
    attribute_ids = []
    channel_ids = []

    # when
    result_data = get_products_data(
        products, export_fields, attribute_ids, warehouse_ids, channel_ids
    )

    # then
    expected_data = []
    for product in products.order_by("pk"):
        product_data = {"id": product.pk}

        for variant in product.variants.all():
            data = {"variants__sku": variant.sku}
            data.update(product_data)

            data = add_stocks_to_expected_data(data, variant, warehouse_ids)

            expected_data.append(data)

    for res in result_data:
        assert res in expected_data


def test_get_products_data_for_specified_warehouses_channels_and_attributes(
    product,
    variant_with_many_stocks,
    product_with_image,
    product_with_variant_with_two_attributes,
    file_attribute,
    product_type_page_reference_attribute,
    product_type_product_reference_attribute,
    page_list,
):
    # given
    product.variants.add(variant_with_many_stocks)
    product.product_type.variant_attributes.add(
        file_attribute,
        product_type_page_reference_attribute,
        product_type_product_reference_attribute,
    )
    product.product_type.product_attributes.add(
        file_attribute,
        product_type_page_reference_attribute,
        product_type_product_reference_attribute,
    )

    # add file attribute
    associate_attribute_values_to_instance(
        variant_with_many_stocks, file_attribute, file_attribute.values.first()
    )
    associate_attribute_values_to_instance(
        product, file_attribute, file_attribute.values.first()
    )

    # add page reference attribute
    product_page_ref_value = AttributeValue.objects.create(
        attribute=product_type_page_reference_attribute,
        slug=f"{product.pk}_{page_list[0].pk}",
        name=page_list[0].title,
    )
    variant_page_ref_value = AttributeValue.objects.create(
        attribute=product_type_page_reference_attribute,
        slug=f"{variant_with_many_stocks.pk}_{page_list[1].pk}",
        name=page_list[1].title,
    )
    associate_attribute_values_to_instance(
        variant_with_many_stocks,
        product_type_page_reference_attribute,
        variant_page_ref_value,
    )
    associate_attribute_values_to_instance(
        product, product_type_page_reference_attribute, product_page_ref_value
    )

    # add product reference attribute
    variant_product_ref_value = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        slug=(
            f"{variant_with_many_stocks.pk}"
            f"_{product_with_variant_with_two_attributes.pk}"
        ),
        name=product_with_variant_with_two_attributes.name,
    )
    product_product_ref_value = AttributeValue.objects.create(
        attribute=product_type_product_reference_attribute,
        slug=f"{product.pk}_{product_with_image.pk}",
        name=product_with_image.name,
    )
    associate_attribute_values_to_instance(
        variant_with_many_stocks,
        product_type_product_reference_attribute,
        variant_product_ref_value,
    )
    associate_attribute_values_to_instance(
        product, product_type_product_reference_attribute, product_product_ref_value
    )

    products = Product.objects.all()
    export_fields = {"id", "variants__sku"}
    warehouse_ids = [str(warehouse.pk) for warehouse in Warehouse.objects.all()]
    attribute_ids = [str(attr.pk) for attr in Attribute.objects.all()]
    channel_ids = [str(channel.pk) for channel in Channel.objects.all()]

    # when
    result_data = get_products_data(
        products, export_fields, attribute_ids, warehouse_ids, channel_ids
    )

    # then
    expected_data = []
    for product in products.order_by("pk"):
        product_data = {"id": product.id}

        product_data = add_product_attribute_data_to_expected_data(
            product_data, product, attribute_ids
        )
        product_data = add_channel_to_expected_product_data(
            product_data, product, channel_ids
        )

        for variant in product.variants.all():
            data = {"variants__sku": variant.sku}
            data.update(product_data)

            data = add_stocks_to_expected_data(data, variant, warehouse_ids)
            data = add_variant_attribute_data_to_expected_data(
                data, variant, attribute_ids
            )
            data = add_channel_to_expected_variant_data(data, variant, channel_ids)

            expected_data.append(data)

    assert result_data == expected_data
